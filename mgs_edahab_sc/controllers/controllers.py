# -*- coding: utf-8 -*-
from odoo import http
import json
from datetime import datetime, date
from odoo.http import request
import werkzeug.wrappers
import logging
import pytz
from odoo.exceptions import AccessDenied, AccessError
# from odoo.addons.mgs_user_access_token.controllers.controllers import validate_token

_logger = logging.getLogger(__name__)


class MgsEdahabIntegration(http.Controller):

    def edahab_authenticate(self, key, db):
        payment_provider = request.env.ref('mgs_edahab_sc.payment_provider_edahab_sc')
        _logger.info(payment_provider) 
        user_id = payment_provider.sudo().edahab_sc_user_id
        try:
            request.session.authenticate(db, user_id.login, key)
        except AccessError as aee:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),("Pragma", "no-cache")],
                response=json.dumps({'error_message': str(aee.name)}))
            
            
        except AccessDenied as ade:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),("Pragma", "no-cache")],
                response=json.dumps({'error_message': "Access denied"}))
        
        
        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {'success_message': "Authenticate"}),)


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

    @http.route('/api/edahab/property', methods=["GET", "POST"], type='http',  auth="public", csrf=False)
    def customer_balance_info(self, property_id, **kw):
        db = request._cr.dbname
        headers = request.httprequest.headers
        authenticate = self.edahab_authenticate(headers.get('edahabkey'), db)
        tenant_id = request.env['res.partner'].sudo().search([('property_id.name', '=', property_id)], limit=1)
        
        if authenticate.status_code == 200:
            if not tenant_id:
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"),("Pragma", "no-cache")],
                    response=json.dumps({"error_message": "Invalid property Number"}))
                
                
            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                response=json.dumps(
                    {
                        "partner": tenant_id.name,
                        "balance": round(request.env['mgs.payment.base'].get_partner_balance(tenant_id.id), 4)
                    }
                ))
        else:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),("Pragma", "no-cache")],
                response=json.dumps({"error_message": "Authentication failed, Invalid credentials or revoked Access"}))
            
            
            
    @http.route('/api/edahab/payment', methods=["GET", "POST"], type='http',  auth="none", csrf=False)
    def payment(self, **kw):
        db = request._cr.dbname
        headers = request.httprequest.headers
        authenticate = self.edahab_authenticate(headers.get('edahabkey'), db)
        """
        Body [meter_no, amount_paid, date, transaction_id, sender_mobile]
        """
        if authenticate.status_code != 200:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),("Pragma", "no-cache")],
                response=json.dumps({"error_message": "Authentication failed, Invalid credentials or revoked Access"})
            )

        body = json.loads(request.httprequest.data)
        tenant_id = request.env['res.partner'].sudo().search([('property_id.name', '=', body.get('meter_no'))], limit=1)
        
        if not tenant_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),("Pragma", "no-cache")],
                response=json.dumps({"error_message": "Invalid meter number",})
            )
            
            
        if float(body.get('amount_paid')) <= 0.0:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),("Pragma", "no-cache")],
                response=json.dumps({"error_message": "Amount can not be negative or zero",}),)
            
            
        payment_provider = request.env.ref('mgs_edahab_sc.payment_provider_edahab_sc')
        
        if not payment_provider.sudo().journal_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                response=json.dumps({"error_message": "Can not complete this request"})
            )

        input_date = datetime.strptime(body.get('date'), '%m-%d-%Y %H:%M:%S')
        input_timezone = pytz.timezone('Africa/Mogadishu')
        # Convert the input date to UTC timezone
        utc_date = input_timezone.localize(input_date).astimezone(pytz.UTC)
        
        try:
            payment_id = request.env['mgs.payment.transaction'].sudo().create({
                'name': body.get('transaction_id'),
                'partner_id': tenant_id.id if tenant_id else None,
                'amount': body.get('amount_paid'),
                'paid_by': body.get('sender_mobile'),
                'ref': body.get('transaction_id'),
                'meter_no': body.get('meter_no'),
                'date': utc_date.replace(tzinfo=None),
                'method_id': payment_provider.id,
                'journal_id': payment_provider.journal_id.id
            })
           
            if payment_id.state == 'duplicate':
                _logger.error("---------------Edahab Short Code Transaction Failed (Duplicate Payment)---------------")
                payment_id.sudo().unlink()
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"),("Pragma", "no-cache")],
                    response=json.dumps({"error_message": "Duplicate Payment"}))
                
            
            _logger.info("---------------Edahab Short Code Transaction Success---------------")
            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                response=json.dumps({
                    "success_message": "Transaction created successfully",
                    "necsom_transaction_id": payment_id.id}))
            
            
        except Exception as e:
            _logger.error("---------------Edahab Short Code Transaction Failed---------------")
            
            _logger.error(str(e))
            error_log = self.create_log(
                request.httprequest.url,
                str(request.httprequest.method).lower(), 
                request.httprequest.remote_addr,str(e)
            )
            
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                response=json.dumps({"error_message": "Transaction Process Failed", "error_reference": error_log.name}))
        
