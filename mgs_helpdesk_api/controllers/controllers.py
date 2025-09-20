# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import pytz
from datetime import datetime, date, timedelta
from odoo import fields
from dateutil.relativedelta import relativedelta
import logging
from werkzeug.exceptions import BadRequest, NotFound, Forbidden 
_logger = logging.getLogger(__name__)



class MgsHelpdeskApi(http.Controller):

    def _validate_user_access(self, ticket_id=None):
        """Validate user has access to the requested resource"""
        current_user = request.env.user        
        if ticket_id:
            ticket = request.env['helpdesk.ticket'].sudo().browse(ticket_id)
            if not ticket:
                raise NotFound("Ticket not found")
            if current_user.id != ticket.user_id.id:
                raise Forbidden("You don't have access to this ticket")
        return current_user

    @http.route("/helpdeskapi/tickets", auth="user", type="json", methods=['GET'])
    def get_tickets(self, **kw):
        """
        Get tickets with optional filtering
        ---
        tags:
          - Tickets
        parameters:
          - name: ticket_id
            in: query
            type: integer
            required: false
            description: Specific ticket ID to retrieve
          - name: user_id
            in: query
            type: integer
            required: false
            description: Filter by assigned user
          - name: stage
            in: query
            type: string
            required: false
            description: Filter by stage name
        responses:
          200:
            description: List of tickets or single ticket details
          400:
            description: Invalid request parameters
          403:
            description: Unauthorized access
          404:
            description: Ticket not found
        """
        try:
            current_user = self._validate_user_access(kw.get('ticket_id'))
            
            # Get the current user and their timezone
            user_tz = current_user.tz or 'UTC'
            user_timezone = pytz.timezone(user_tz)
            utc_timezone = pytz.UTC

            def convert_utc_to_user_tz(utc_datetime, user_timezone):
                """Convert UTC datetime to user's timezone"""
                if not utc_datetime:
                    return None
                if utc_datetime.tzinfo is None:
                    utc_datetime = utc_timezone.localize(utc_datetime)
                return utc_datetime.astimezone(user_timezone)

            ticket_obj = request.env["helpdesk.ticket"]
            
            # If specific ticket requested
            if kw.get("ticket_id"):
                domain = [("id", "=", int(kw.get("ticket_id")))]
                ticket_records = ticket_obj.sudo().search(domain, limit=1)
                
                if not ticket_records:
                    raise NotFound("Ticket not found")
                
                tickets = []
                for record in ticket_records:
                    # Full details for single ticket
                    create_date_user_tz = convert_utc_to_user_tz(record.create_date, user_timezone)
                    # start_date_user_tz = convert_utc_to_user_tz(record.planned_date_begin, user_timezone)
                    # end_date_user_tz = convert_utc_to_user_tz(record.date_deadline, user_timezone)
                    
                    tickets.append({
                        "id": record.id,
                        "name": record.name,
                        "create_date": create_date_user_tz,
                        "description": record.description,
                        "qr_code": record.qr_code,
                        "priority": record.priority,
                        "stage_name": record.stage_id.name if record.stage_id else None,
                        "partner_name": record.partner_id.name if record.partner_id else None,
                        "partner_phone": record.partner_id.phone if record.partner_id else None,
                        "partner_id": record.partner_id.id if record.partner_id else None,
                        "partner_latitude": record.partner_id.partner_latitude if record.partner_id else None,
                        "partner_longitude": record.partner_id.partner_longitude if record.partner_id else None,
                        "start_date": False,
                        "end_date": False,
                        "allocated_time": False,
                    })
                return tickets[0] if tickets else {}
            
            # Multiple tickets (list view)
            domain = []
            if kw.get("user_id"):
                domain.append(("user_id", "=", kw.get("user_id")))
            if kw.get("stage"):
                domain.append(("stage_id.name", "=", kw.get("stage")))
            
            limit = 100
            page = kw.get("page", 1)
            ticket_records = ticket_obj.sudo().search(domain, limit=limit)
            
            tickets = []
            for record in ticket_records:
                # Basic details for list view
                tickets.append({
                    "id": record.id,
                    "name": record.name,
                    "create_date": record.create_date,
                    "description": record.description,
                    "priority": record.priority,
                    "stage_name": record.stage_id.name if record.stage_id else None,
                    "partner_name": record.partner_id.name if record.partner_id else None,
                    "partner_phone": record.partner_id.phone if record.partner_id else None,
                })
            
            return tickets

        except (ValueError, TypeError) as e:
            raise BadRequest("Invalid request parameters: %s" % str(e))
        except Exception as e:
            _logger.error("Error getting tickets: %s", str(e))
            raise

    @http.route("/helpdeskapi/tickets", auth="user", type="json", methods=['PATCH'])
    def update_ticket(self, **kw):
        """
        Update ticket with various actions
        ---
        tags:
          - Tickets
        parameters:
          - name: ticket_id
            in: body
            type: integer
            required: true
            description: ID of ticket to update
          - name: action
            in: body
            type: string
            required: true
            enum: [start, finish, suspend, update_content, accept, reject]
            description: Action to perform on the ticket
        responses:
          200:
            description: Ticket updated successfully
          400:
            description: Invalid action or missing parameters
          403:
            description: Unauthorized access
          404:
            description: Ticket not found
        """
        try:
            ticket_id = kw.get("ticket_id")
            if not ticket_id:
                raise BadRequest("ticket_id is required")
            
            current_user = self._validate_user_access(ticket_id)
            ticket_obj = request.env["helpdesk.ticket"].sudo().search([("id", "=", int(ticket_id))], limit=1)
            
            if not ticket_obj:
                raise NotFound("Ticket not found")
            
            action = kw.get("action")
            if not action:
                raise BadRequest("action is required")
            
            if action == "start":
                in_progress_stage = request.env.company.in_progress_stage_id
                if not in_progress_stage:
                    raise BadRequest("In progress stage not configured")
                ticket_obj.stage_id = in_progress_stage
                return {"success": True, "message": "Ticket started"}
                
            elif action == "finish":
                done_stage = request.env.company.done_stage_id
                if not done_stage:
                    raise BadRequest("Done stage not configured")
                ticket_obj.stage_id = done_stage
                if kw.get("comments"):
                    ticket_obj.message_post(body=f"Comment: {kw.get('comments')}")
                return {"success": True, "message": "Ticket finished"}
                
            elif action == "suspend":
                suspended_stage = request.env.company.suspended_stage_id
                if not suspended_stage:
                    raise BadRequest("Suspended stage not configured")
                ticket_obj.stage_id = suspended_stage
                return {"success": True, "message": "Ticket suspended"}
                
            elif action == "accept":
                ticket_obj.accepted_rejected_state = "accepted"
                return {"success": True, "message": "Ticket accepted"}
                
            elif action == "update_content":
                if kw.get("comment"):
                    # ticket_obj.description = kw.get("comment")
                    ticket_obj.message_post(body=f"Comment From Update: {kw.get('comment')}")
                
                if kw.get("qr_code"):
                    ticket_obj.qr_code = kw.get("qr_code")
                
                # Handle images
                if kw.get("image") and kw.get("image_type"):
                    if kw.get("image_type") not in ["Before Work", "After Work"]:
                        raise BadRequest("Invalid image_type. Must be 'Before Work' or 'After Work'")
                    
                    image_name = kw.get("image_name") or f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    html_content = f'''
                        <div style="max-width:100%; overflow:hidden;">
                            <img src="data:image/png;base64,{kw.get("image")}" alt="{kw.get("image_type")} Image" style="max-width:100%; height:auto; object-fit:contain;"/>
                        </div>
                    '''
                    
                    if kw.get("image_type") == "Before Work":
                        ticket_obj.before_work_start_image = html_content
                        ticket_obj.before_work_start_image_base64 = kw.get("image")
                    elif kw.get("image_type") == "After Work":
                        ticket_obj.after_work_end_image = html_content
                        ticket_obj.after_work_end_image_base64 = kw.get("image")
                
                # Handle coordinates
                coordinate_fields = [
                    ('pre_work_lat', 'prework_lat'),
                    ('pre_work_lon', 'prework_lon'),
                    ('post_work_lat', 'post_work_lat'),
                    ('post_work_lon', 'post_work_lon')
                ]
                
                for kw_field, ticket_field in coordinate_fields:
                    if kw.get(kw_field):
                        setattr(ticket_obj, ticket_field, kw.get(kw_field))
                
                return {"success": True, "message": "Ticket updated successfully"}
            
            else:
                raise BadRequest("Invalid action specified")
                
        except Exception as e:
            _logger.error("Error updating ticket: %s", str(e))
            raise

    @http.route("/helpdeskapi/tickets/attachments", auth="user", type="json", methods=['GET'])
    def get_ticket_attachments(self, **kw):
        """
        Get ticket attachments
        ---
        tags:
          - Attachments
        parameters:
          - name: ticket_id
            in: query
            type: integer
            required: true
            description: ID of the ticket
        responses:
          200:
            description: List of attachments
          400:
            description: Missing ticket_id
          403:
            description: Unauthorized access
          404:
            description: Ticket not found
        """
        try:
            ticket_id = kw.get("ticket_id")
            if not ticket_id:
                raise BadRequest("ticket_id is required")
            
            current_user = self._validate_user_access(ticket_id)
            ticket_obj = request.env["helpdesk.ticket"].sudo().search([("id", "=", int(ticket_id))], limit=1)
            
            if not ticket_obj:
                raise NotFound("Ticket not found")
            
            attachment_data = []
            
            if ticket_obj.before_work_start_image_base64:
                attachment_data.append({
                    "id": "",
                    "name": "FirstImage",
                    "mimetype": "image/png",
                    "datas": ticket_obj.before_work_start_image_base64,
                })
            
            if ticket_obj.after_work_end_image_base64:
                attachment_data.append({
                    "id": "",
                    "name": "SecondImage",
                    "mimetype": "image/png",
                    "datas": ticket_obj.after_work_end_image_base64,
                })

            return {
                "success": True,
                "ticket_id": ticket_id,
                "attachments": attachment_data,
            }

        except Exception as e:
            _logger.error("Error getting attachments: %s", str(e))
            raise

    @http.route("/helpdeskapi/tickets/attachments", auth="user", type="json", methods=['DELETE'])
    def delete_ticket_attachments(self, **kw):
        """
        Delete ticket attachments
        ---
        tags:
          - Attachments
        parameters:
          - name: ticket_id
            in: body
            type: integer
            required: true
            description: ID of the ticket
          - name: name
            in: body
            type: string
            required: true
            enum: [FirstImage, SecondImage]
            description: Name of attachment to delete
        responses:
          200:
            description: Attachment deleted successfully
          400:
            description: Missing parameters
          403:
            description: Unauthorized access
          404:
            description: Ticket not found
        """
        try:
            ticket_id = kw.get("ticket_id")
            if not ticket_id:
                raise BadRequest("ticket_id is required")
            
            attachment_name = kw.get("name")
            if not attachment_name:
                raise BadRequest("name is required")
            
            current_user = self._validate_user_access(ticket_id)
            ticket_obj = request.env["helpdesk.ticket"].sudo().search([("id", "=", int(ticket_id))], limit=1)
            
            if not ticket_obj:
                raise NotFound("Ticket not found")
            
            if attachment_name == "FirstImage":
                ticket_obj.before_work_start_image = ""
                ticket_obj.before_work_start_image_base64 = ""
            elif attachment_name == "SecondImage":
                ticket_obj.after_work_end_image = ""
                ticket_obj.after_work_end_image_base64 = ""
            else:
                raise BadRequest("Invalid attachment name")
            
            return {
                "success": True,                
                "message": "Ticket Attachment Removed Successfully!",
            }

        except Exception as e:
            _logger.error("Error deleting attachment: %s", str(e))
            raise

    @http.route("/helpdeskapi/profile", auth="user", type="json", methods=['GET'])
    def get_user_profile(self, **kw):
        """
        Get user profile data
        ---
        tags:
          - Profile
        responses:
          200:
            description: User profile data
          403:
            description: Unauthorized access
        """
        try:   
            current_user = self._validate_user_access()
            
            return {
                "success": True, 
                "data": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "username": current_user.login,
                    "image": current_user.image_1920,
                    "fcm_token": getattr(current_user, 'fcm_token', None),
                }
            }

        except Exception as e:
            _logger.error("Error getting user profile: %s", str(e))
            raise

    @http.route("/helpdeskapi/profile", auth="user", type="json", methods=['PATCH'])
    def update_user_profile(self, **kw):
        """
        Update user profile
        ---
        tags:
          - Profile
        parameters:
          - name: name
            in: body
            type: string
            required: false
            description: New full name
          - name: username
            in: body
            type: string
            required: false
            description: New username
          - name: image
            in: body
            type: string
            required: false
            description: Base64 encoded image
          - name: fcm_token
            in: body
            type: string
            required: false
            description: New FCM token
          - name: new_password
            in: body
            type: string
            required: false
            description: New password
          - name: current_password
            in: body
            type: string
            required: false
            description: Current password (required for password change)
        responses:
          200:
            description: Profile updated successfully
          400:
            description: Invalid input or missing current password
          403:
            description: Unauthorized access
        """
        try:
            current_user = self._validate_user_access()
            update_values = {}
            
            # Handle basic profile updates
            # if kw.get("name"):
            #     update_values['name'] = kw.get("name")
            
            # if kw.get("username"):
            #     update_values['login'] = kw.get("username")
            
            if kw.get("image"):
                update_values['image_1920'] = kw.get("image")
            
            if kw.get("fcm_token"):
                update_values['fcm_token'] = kw.get("fcm_token")
            
            # Handle password change
            if kw.get("new_password"):
                if not kw.get("current_password"):
                    raise BadRequest("Current password is required to change password")
                
                # In a real implementation, you would verify current password first
                update_values['password'] = kw.get("new_password")
            
            # Apply updates
            if update_values:
                current_user.sudo().write(update_values)
            
            return {
                "success": True,
                "message": "Profile updated successfully"
            }

        except Exception as e:
            _logger.error("Error updating profile: %s", str(e))
            raise

    @http.route("/helpdeskapi/dashboard", auth="user", type="json", methods=['GET'])
    def dashboard(self, **kw):
        """
        Get dashboard statistics
        ---
        tags:
          - Dashboard
        parameters:
          - name: user_id
            in: query
            type: integer
            required: true
            description: ID of the user
        responses:
          200:
            description: Dashboard statistics
          400:
            description: Missing user_id
          403:
            description: Unauthorized access
        """
        try:
            if not kw.get("user_id"):
                raise BadRequest("user_id is required")
            
            current_user = self._validate_user_access()
            
            stage_obj = request.env["helpdesk.stage"].sudo().search([
                ("active", "=", True), 
                ("does_appear_in_mobile", '=', True)                
            ]).read(["id", "name"])         
            
            dashboard = {}
            for stage in stage_obj:
                counter = request.env["helpdesk.ticket"].sudo().search_count([
                    ("user_id", "=", kw.get("user_id")), 
                    ("stage_id.id", "=", stage["id"]),
                ])
                dashboard[stage["name"]] = counter
                
            done_stage = request.env.company.done_stage_id
            today = date.today()

            ticket_count = request.env['helpdesk.ticket'].search_count([
                ('stage_id', '=', done_stage.id),
                ('user_id', '=', kw.get("user_id")),
                ('date_last_stage_update', '>=', today),
                ('date_last_stage_update', '<', today + relativedelta(days=1)),
            ])
            
            return dashboard

        except Exception as e:
            _logger.error("Error getting dashboard data: %s", str(e))
            raise

    @http.route("/helpdeskapi/partners/coordinates", auth="user", type="json", methods=['PATCH'])
    def update_partner_coordinates(self, **kw):
        """
        Update partner coordinates
        ---
        tags:
          - Partners
        parameters:
          - name: ticket_id
            in: body
            type: integer
            required: true
            description: ID of the related ticket
          - name: lat
            in: body
            type: number
            required: true
            description: New latitude
          - name: lon
            in: body
            type: number
            required: true
            description: New longitude
        responses:
          200:
            description: Coordinates updated successfully
          400:
            description: Missing parameters
          403:
            description: Unauthorized access
          404:
            description: Ticket or partner not found
        """
        try:
            ticket_id = kw.get("ticket_id")
            if not ticket_id:
                raise BadRequest("ticket_id is required")
            
            if not kw.get("lat") or not kw.get("lon"):
                raise BadRequest("lat and lon are required")
            
            current_user = self._validate_user_access(ticket_id)
            ticket_obj = request.env["helpdesk.ticket"].sudo().search([("id", "=", int(ticket_id))], limit=1)
            
            if not ticket_obj:
                raise NotFound("Ticket not found")
            
            partner = ticket_obj.partner_id
            if not partner:
                raise NotFound("No partner found for this ticket")
            
            lat = float(kw.get("lat"))
            lon = float(kw.get("lon"))
            
            partner.partner_latitude = lat
            partner.partner_longitude = lon
            
            return {
                "success": True, 
                "message": "Partner coordinates updated successfully"
            }

        except (ValueError, TypeError) as e:
            raise BadRequest("Invalid coordinates format")
        except Exception as e:
            _logger.error("Error updating coordinates: %s", str(e))
            raise

    @http.route("/helpdeskapi/attendance", auth="user", type="json", methods=['POST'])
    def attendance_checkin_checkout(self, **kw):
        """
        Record attendance check-in or check-out
        ---
        tags:
          - Attendance
        parameters:
          - name: punch_state
            in: body
            type: string
            required: true
            enum: [in, out]
            description: Whether checking in or out
          - name: lat_in
            in: body
            type: number
            required: false
            description: Latitude for check-in
          - name: lon_in
            in: body
            type: number
            required: false
            description: Longitude for check-in
          - name: lat_out
            in: body
            type: number
            required: false
            description: Latitude for check-out
          - name: lon_out
            in: body
            type: number
            required: false
            description: Longitude for check-out
        responses:
          200:
            description: Attendance recorded successfully
          400:
            description: Invalid punch state or missing employee record
          403:
            description: Unauthorized access
        """
        try:
            current_user = self._validate_user_access()
            punch_state = kw.get("punch_state")
            
            if punch_state not in ['in', 'out']:
                raise BadRequest("Invalid punch state. Must be 'in' or 'out'")
            
            employee_id = current_user.employee_id  
            if not employee_id:
                raise BadRequest("No Employee Record for the User")
            
            attendance_obj = request.env["hr.attendance"]
            check_in_out_datetime = fields.Datetime.now()
                        
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)           
            oatt_domain = [
                ('employee_id', '=', current_user.employee_id.id), 
                ('check_in','!=',False),
                ('check_out', '=', False)
            ]
            open_att = attendance_obj.sudo().search(oatt_domain, limit=1)  
            
            # Check for CLOSED attendance today (already has check-in & check-out)
            closed_att_domain = [
                ('employee_id', '=', current_user.employee_id.id),
                ('check_in', '>=', today_start),
                ('check_in', '<', today_end),
                ('check_out', '!=', False)
            ]
            closed_att = attendance_obj.sudo().search(closed_att_domain, limit=1)              
            
            if punch_state == "in":
                if closed_att:
                    return {
                        "success": True, 
                        "message": "Already recorded attendance for the employee today."
                    }
                
                if not open_att:
                    attendance_obj.sudo().create({
                        'employee_id': employee_id.id,
                        'check_in': check_in_out_datetime,
                        'in_latitude': kw.get("lat_in"),
                        'in_longitude': kw.get("lon_in"),
                    })
                
                if open_att and check_in_out_datetime >= open_att.check_in + timedelta(hours=20):
                    open_att.check_out = open_att.check_in
                    attendance_obj.sudo().create({
                        'employee_id': employee_id.id,
                        'check_in': check_in_out_datetime
                    })

            if punch_state == "out":
                if not open_att:
                    raise BadRequest("No open attendance record to check out from")
                
                open_att.check_out = check_in_out_datetime
                open_att.out_latitude = kw.get("lat_out")
                open_att.out_longitude = kw.get("lon_out")

            return {
                'success': True, 
                'message': 'Attendance recorded'
            }
        
        except Exception as e:
            _logger.error(f"Attendance error: {e}")
            raise
          
          
          
          