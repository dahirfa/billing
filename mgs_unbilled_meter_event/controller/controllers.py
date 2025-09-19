# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request
import werkzeug.wrappers as wrap

import logging
_logger = logging.getLogger(__name__)


class Mgs_Unbilled_Meter_Event_Controller(http.Controller):
    
    
    @http.route('/billingApi/unbilledmeterevent/', type='json', auth='user', methods=['POST'], csrf=False)
    def create_unbilled_meter_event(self, **kw):
        
        unbilled_meter_event_obj = http.request.env['mgs.meter.event.blocking']
        
        collector_id = self.get_user_partner_id(request.session.uid)
        
        property_id = kw.get("property")
        reason_id = kw.get("reason")        
        
        domain = [('name', '=', property_id.upper()), ('zone_id.collector_ids.ids', 'in', collector_id), ('state', '=', 'connected')]        
        
        property_id = http.request.env['mgs_billing.property'].sudo().search(domain, limit=1)
        
        if not property_id:
            return "Invalid Home Number or Home is not Connected."
        try:
            created_reading = unbilled_meter_event_obj.sudo().create({
                'property_id': property_id.id,                
                'reason_id': reason_id,                
                'user_id': request.session.uid,                
            })
            
            return {                
                'response': 'Success'
            }
        
        except Exception as e:
            return {
                "error": "ERROR: "+str(e),
                'response': 'Fail'
            }
        
          
    def get_user_partner_id(self, user):
        user_id = request.env['res.users'].search([('id', '=', user)])
        return user_id.partner_id.id if user_id else None    
        
        
    @http.route('/billingApi/meter_event_blocking_reasons', type='http', auth='public', methods=['GET'], csrf=False)
    def get_meter_event_blocking_reasons(self, **kwargs):
        try:
            # Query your model
            reasons = request.env['mgs.meter.event.blocking.reason'].sudo().search([])
            
            # Prepare data
            data = [{'id': r.id, 'name': r.name} for r in reasons]

            return request.make_response(
                json.dumps({'status': 'success', 'data': data}),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers=[('Content-Type', 'application/json')]
            )
        