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


class MgsTPlusIntegration(http.Controller):

    def mycash_authenticate(self, key, db):
        payment_method = request.env.ref(
            'mgs_mycash_integration.payment_provider_mycash')
        user_id = payment_method.sudo().mycash_user_id
        try:
            request.session.authenticate(db, user_id.login, key)
        except AccessError as aee:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),
                         ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        'msg': "Error: %s" % aee.name
                    }),)
        except AccessDenied as ade:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),
                         ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        'msg': "Error: Access denied"
                    }),)
        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {'response': "Authenticate"}),)
    # Bill
    # @validate_token

    @http.route('/api/values/mycash/getinfo/<int:meter>', methods=["GET", "POST"], type='http',  auth="public", csrf=False)
    def bill_info(self, meter, **kw):
        db = request._cr.dbname
        headers = request.httprequest.headers
        authenticate = self.mycash_authenticate(headers.get('key'), db)

        if authenticate.status_code != 200:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),
                         ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "error": "Authentication failed, Invalid credentials or revoked Access",
                    }),)

        tenant_id = request.env['res.partner'].sudo().search(
            [('property_id.name', '=', meter)], limit=1)
        #
        if not tenant_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),
                         ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "validResponse": True,
                        "statusCode": "400",
                        "statusMessage": "Invalid meterno"
                    }),)

        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            response=json.dumps(
                {
                    "customerName": tenant_id.name,
                    "balance": round(request.env['mgs.payment.base'].get_partner_balance(tenant_id.id), 4)
                }
            ))
        # else:
        #     return werkzeug.wrappers.Response(
        #         status=400,
        #         content_type="application/json; charset=utf-8",
        #         headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
        #         response=json.dumps(
        #             {
        #                 "error": "Authentication failed, Invalid credentials or revoked Access",
        #             }),)

    # @validate_token
    @http.route('/api/values/mycash/paymentinfo', methods=["GET", "POST"], type='http',  auth="none", csrf=False)
    def payment_info(self, **kw):
        db = request._cr.dbname
        headers = request.httprequest.headers
        authenticate = self.mycash_authenticate(headers.get('key'), db)
        if authenticate.status_code != 200:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),
                         ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "error": "Authentication failed, Invalid credentials or revoked Access",
                    }),)

        body = json.loads(request.httprequest.data)
        tenant_id = request.env['res.partner'].sudo().search(
            [('property_id.name', '=', body.get('MeterNo'))], limit=1)
        if not tenant_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),
                         ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "error": "Invalid meterno",
                    }),)
        if float(body['AmountPaid']) <= 0.0:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),
                         ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "error": "Amount can not be negative or zero",
                    }),)
        payment_method = request.env.ref(
            'mgs_mycash_integration.payment_provider_mycash')
        if not payment_method.sudo().journal_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                response=json.dumps(
                    {
                        "error": "Can not cmplete this request",
                    }
                ))

        input_date = datetime.strptime(body['Date'], '%m-%d-%Y %H:%M:%S')
        input_timezone = pytz.timezone('Africa/Mogadishu')
        # Convert the input date to UTC timezone
        utc_date = input_timezone.localize(input_date).astimezone(pytz.UTC)
        payment_id = request.env['mgs.payment.transaction'].sudo().create({
            'name': body['MyCashID'],
            'partner_id': tenant_id.id if tenant_id else None,
            'amount': body['AmountPaid'],
            'ref': body['MyCashID'],
            'meter_no': body['MeterNo'],
            'date': utc_date.replace(tzinfo=None),
            'method_id': payment_method.id,
            'journal_id': payment_method.journal_id.id
        })
        if not payment_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                response=json.dumps(
                    {
                        "error": "Can not complete this request",
                    }))
        if payment_id.state == 'duplicate':
            payment_id.sudo().unlink()
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),
                         ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "statuscode": "400",
                        "statusmessage": "error - Duplicate Payment",
                    }),)
        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            response=json.dumps({
                "isSuccess": True,
                "message": "Transaction created successfully",
                "necTransactionID": "%s" % payment_id.id}))
