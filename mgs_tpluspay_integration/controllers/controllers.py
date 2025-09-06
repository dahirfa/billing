# -*- coding: utf-8 -*-
from odoo import http
import json
from datetime import datetime, date
from odoo.http import request
import werkzeug.wrappers
import logging
import requests
from requests.exceptions import ConnectionError, HTTPError
from odoo.exceptions import AccessDenied, AccessError
import pytz
_logger = logging.getLogger(__name__)


class MGSTplusPayIntegrationPayBill(http.Controller):
    def get_allowed_partners(self, partner_id):
        return (
            request.env["res.partner"]
            .sudo()
            .search(
                [
                    "|",
                    ("message_partner_ids", "child_of", (partner_id)),
                    ("id", "=", partner_id),
                ]
            )
        )

    def check_reading_access(self, user_partner, partner_id):
        allowed_partner_ids = self.get_allowed_partners(user_partner)
        if not allowed_partner_ids:
            return False
        elif partner_id not in allowed_partner_ids.ids:
            return False
        return True
    
    
    def convert_date(self, date):
        parsed_date = datetime.strptime(date, "%b %d %Y %I:%M%p")       
        input_timezone = pytz.timezone('Africa/Mogadishu')
        localized_date = input_timezone.localize(parsed_date)
        utc_date = localized_date.astimezone(pytz.UTC)
        return utc_date.replace(tzinfo=None)
    
    
    def create_log(self, end_point, request_type, request_ip, error_message):
        values = {
            "date": datetime.now(),
            "end_point": end_point,
            "request_type": request_type,
            "request_ip": request_ip,
            "error_message": error_message,
        
        }
        error_log = request.env["mgs.integration.log"].sudo().create(values)# Log Errors
        
        return error_log
    
    
    def tpluspay_authenticate(self):
        payment_provider = request.env.ref('mgs_tpluspay_integration.payment_provider_tpluspay').sudo()
        
        user_id = payment_provider.tpluspay_user_id
        password = payment_provider.tpluspay_pass
        auth_url = payment_provider.auth_url
         

        payload = json.dumps({
            "username": user_id,
            "password": password,
            "browserId": ""
        })
        headers = {
        'Content-Type': 'application/json'
        }

        try:
            response = requests.post(auth_url, headers=headers, data=payload)
            response.raise_for_status()  # Raises an error for non-2xx responses
            response_data = response.json()
            
            # Check for successful authentication
            if response_data.get("responsecode") == "000":
                response_json = json.loads(response_data.get("responsejson", "{}"))
                return {
                    "token": response_json.get("Token"),
                    "payment_url": response_json.get("PUrl"),
                    "error": None
                }
            else:
                # Return error message from response if authentication failed
                return {
                    "status": response_data.get("responsecode"),
                    "error_message": response_data.get("responsedesc")
                }
        
        except requests.RequestException as e:
            # Handle network issues or other request exceptions
            return {
                "status": "error",
                "error_message": str(e)
            }
        

    
    
    @http.route("/api/tpluspay/paybill", methods=["GET", "POST"], type="json", auth="user", csrf=False)
    def paybilltplus(self, **kw):
        
        auth_data = self.tpluspay_authenticate()
        payment_provider = request.env.ref('mgs_tpluspay_integration.payment_provider_tpluspay')        
        # Check if an error was returned
        if auth_data["error"]:
            return {
                "status": auth_data["status"],
                "error_message": auth_data["error"]
            }
        
        partner_id = int(kw.get("partner_id"))
        
        user_partner = (
            request.env["res.users"]
            .search([("id", "=", request.session.uid)], limit=1)
            .commercial_partner_id.id
        )
        
        if partner_id != user_partner and self.check_reading_access(user_partner, partner_id) == False:
            return {
                "status": 401,
                "error_message": "You are not authorized to create this document.",
            }
            
        if not kw.get("partner_id", False):
            return {
                "status": 400,
                "error_message": "Please provide a partner_id.",
            }
        
        
        if float(kw.get("amount")) <= 0.0:
            return {
                'status': 400,
                "error_message": "Amount can not be negative or zero",
            }
        
        partner = request.env['res.partner'].sudo().search([('property_id.name', '=', kw.get("meter_no"))], limit=1)
        
        if not partner:
            return {"error": "Invalid meterno"}
            
        request_data = {
            "partner_id": partner_id,
            "meter_no": kw.get("meter_no"),
            "amount": kw.get("amount"),
        }
        
        sale_details_url = payment_provider.sudo().sale_details
        success_url = payment_provider.sudo().success_url
        error_url = payment_provider.sudo().error_url
        
        
        payload = json.dumps({
            "amount": request_data["amount"],
            "successUrl": success_url,
            "failureUrl": error_url,
            "callBackUrl": "",
            "deviceType": "web",
            "sheduledId": "",
            "clientId": str(partner.id),
            "productName": "Necsom Tpluspay Payment",
            "token": auth_data["token"]
        })
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            # Make the POST request
            response = requests.post(sale_details_url, headers=headers, data=payload)
            response.raise_for_status() 

            
            response_data = response.json()
            response_json = json.loads(response_data.get("responsejson", "{}"))
            product_id = response_json.get("ProductId")
            
            if not product_id:
                _logger.error('------------T-pluspay ERROR------------')
                _logger.error("Product ID not found in the response")
                error_log = self.create_log(
                request.httprequest.url,
                str(request.httprequest.method).lower(), 
                request.httprequest.remote_addr,
                "Product ID not found in the response"
                )
                return {
                    "status": 400,
                    "error_message": "Product ID not found in the response"
                }
                
            final_payment_url = f"{auth_data['payment_url']}?code={product_id}"
            
            temp_payment_data = request.env["temp.payment.data"].sudo().create({
                "partner_id": request_data["partner_id"],
                "amount": request_data["amount"],
                "code": product_id,  # Store the Product ID here
                "meter_no": request_data['meter_no']
            })
            
            return {
                "status": "000",
                "payment_url": final_payment_url,
                "transid": product_id
            }


        except Exception as e:
            _logger.error('------------T-pluspay ERROR------------')
            _logger.error(e)
            # Handle any other exceptions
            error_log = self.create_log(
                request.httprequest.url,
                str(request.httprequest.method).lower(), 
                request.httprequest.remote_addr,str(e)
            )
            return {
                "status": "error",
                "error_message": f"An unexpected error occurred: {e}",
                "error_referebce":error_log.name
            }
            
            
                
    @http.route('/successUrl<string:code>',type='http', auth='public', methods=['GET', 'POST'], csrf=False, website=True)
    def payment_success(self,code=None, **kwargs):
        res_data = {}
        payment_provider = request.env.ref('mgs_tpluspay_integration.payment_provider_tpluspay').sudo()
        trans_details_url = payment_provider.trans_details

        payload = json.dumps({
        "transId": code
        })
        headers = {
        'Content-Type': 'application/json'
        }
        temp_data = request.env["temp.payment.data"].sudo().search([('code', '=', code)], limit=1)
        
        try:
            response = requests.request("POST", trans_details_url, headers=headers, data=payload)
            response_data = response.json()
            _logger.info(response_data)
            # Check for successful authentication
            if response_data.get("responsecode") == "000":
                response_json = json.loads(response_data.get("responsejson", "{}"))
                
                utc_date = self.convert_date(response_json.get("TransDate"))
                from_acc_name = response_json.get("FromAccName")
                tran_amount = response_json.get("TransAmt")
                
                if temp_data :
                    payment_id = request.env['mgs.payment.transaction'].sudo().create({
                    'name': temp_data.code,
                    'partner_id': temp_data.partner_id.id if temp_data.partner_id else None,
                    'amount': float(temp_data.amount),
                    'paid_by': from_acc_name,
                    'ref':temp_data.code,
                    'meter_no': temp_data.meter_no,
                    'date': utc_date.replace(tzinfo=None),
                    'method_id': payment_provider.id,
                    'journal_id': payment_provider.journal_id.id
                })        
                
                  
                    temp_data.unlink()
                    
                    return request.render('mgs_tpluspay_integration.tplussuccess',{"amount":tran_amount, "status":"Success", "reference": code})
                    
                else:
                    res_data = {
                        "status": response_data.get("responsecode"),
                        "success_message": response_data.get("responsedesc")
                    }
                    return request.make_response(json.dumps(res_data), headers=[('Content-Type', 'application/json')])
            
        except Exception as e:
            _logger.error('------------T-pluspay ERROR------------')
            _logger.error(e)
            # Handle any other exceptions
            error_log = self.create_log(
                request.httprequest.url,
                str(request.httprequest.method).lower(), 
                request.httprequest.remote_addr,str(e)
            )
            
            res_data = {
                "status": "error",
                "error_message": f"An unexpected error occurred: {e}",
                "error_reference":error_log.name
            }
            return request.make_response(json.dumps(res_data), headers=[('Content-Type', 'application/json')])

        # return "Payment Success Handled"
    
    
    @http.route('/failureUrl', type='http', auth='public', methods=['GET', 'POST'], csrf=False, website=True)
    def payment_error(self, **kwargs):
        
        return request.render('mgs_tpluspay_integration.tpluserror')