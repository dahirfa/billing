# -*- coding: utf-8 -*-
from odoo import http
import json
from datetime import datetime, date
from odoo.http import request
import werkzeug.wrappers
import logging

from odoo.addons.mgs_user_access_token.controllers.controllers import validate_token

_logger = logging.getLogger(__name__)


class MgsTPlusIntegration(http.Controller):
    # Bill
    @validate_token
    @http.route('/api/values/getinfo', methods=["GET", "POST"], type='http',  auth="none", csrf=False)
    def bill_info(self, **kw):
        request_data = json.loads(request.httprequest.data)
        payment_method = request.env.ref(
            'mgs_t-plus_integration.payment_provider_t_plus')       
        customer_ref = request_data['meterno']

        tenant_id = request.env['res.partner'].sudo().search(
            [('property_id.name', '=', customer_ref)], limit=1)
        if not payment_method.sudo().journal_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),
                         ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "error": "There's an error from our side. if you see this contact our team",
                    }),)
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

        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "meterno": customer_ref,
                    "customername": tenant_id.name,
                    "balance": round(request.env['mgs.payment.base'].get_partner_balance(tenant_id.id), 4)
                }))

    @validate_token
    @http.route('/api/values/paymentinfo', methods=["GET", "POST"], type='http',  auth="none", csrf=False)
    def payment_info(self, **kw):
        request_data = json.loads(request.httprequest.data)
        payment_method = request.env.ref(
            'mgs_t-plus_integration.payment_provider_t_plus')
        customer_ref = request_data['meterno']
        tenant_id = request.env['res.partner'].sudo().search(
            [('property_id.name', '=', customer_ref)], limit=1)
        payment_provider = payment_method.sudo()

        if float(request_data['amount']) <= 0.0:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),
                         ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "error": "Amount can not be negative or zero",
                    }),)
        payment_id = request.env['mgs.payment.transaction'].sudo().create({
            'name': request_data['refno'],
            'partner_id': tenant_id.id if tenant_id else None,
            'amount': float(request_data['amount']),
            'ref': request_data['refno'],
            'date': request_data['date'],
            'method_id': payment_provider.id,
            'journal_id': payment_provider.journal_id.id
        })
        if payment_id.state == 'duplicate':
            payment_id.sudo().unlink()
            return werkzeug.wrappers.Response(
                status=200,
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
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "statuscode": "000",
                    "statusmessage": "success",
                    "transactionid": payment_id.id
                }),)
