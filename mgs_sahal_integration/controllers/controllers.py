# -*- coding: utf-8 -*-
import pytz
from odoo.exceptions import AccessDenied, AccessError
from odoo import http
import json
from datetime import datetime, date
from odoo.http import request
import werkzeug.wrappers
import logging
_logger = logging.getLogger(__name__)


class MgsSahalIntegration(http.Controller):
    # Bill
    def sahal_authenticate(self, key, db):
        payment_method = request.env.ref(
            'mgs_sahal_integration.payment_provider_sahal_scode')
        user_id = payment_method.sudo().sahal_sc_user_id
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

    @http.route('/api/meter/<int:meter>', type='http', clean=True, auth='public')
    def bill_info(self, meter, **kw):
        tenant_id = request.env['res.partner'].sudo().search(
            [('property_id.name', '=', meter)], limit=1)
        db = request._cr.dbname
        headers = request.httprequest.headers
        authenticate = self.sahal_authenticate(headers.get('neckey'), db)
        if authenticate.status_code == 200:
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
        else:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),
                         ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "error": "Authentication failed, Invalid credentials or revoked Access",
                    }),)

    @http.route('/api/payment', methods=['GET', 'POST'], type='http', clean=True, auth='public', csrf=False)
    def payment_info(self, **kw):
        db = request._cr.dbname
        headers = request.httprequest.headers
        authenticate = self.sahal_authenticate(headers.get('neckey'), db)
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
            'mgs_sahal_integration.payment_provider_sahal_scode')
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
            'name': body['TransactionID'],
            'partner_id': tenant_id.id if tenant_id else None,
            'amount': body['AmountPaid'],
            'paid_by': body['SenderMobile'],
            'sender_account': body['SenderAccount'],
            'ref': body['TransactionID'],
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

        # customer_ref = request_data['requestBody']['billInfo']['invoiceId']
        # tenant_id = request.env['res.partner'].sudo().search([('property_id.name', '=', customer_ref)], limit=1)
        # if not tenant_id:

        #     return werkzeug.wrappers.Response(
        #     status=400,
        #     content_type="application/json; charset=utf-8",
        #     response=json.dumps(
        #         {
        #             "requestId": request_id,
        #             "schemaVersion": "1.0",
        #             "responseHeader":
        #                 {
        #                     "timestamp": timestamp,
        #                     "resultCode": "400",
        #                     "resultMessage": "Invalid Pill."
        #                 },
        #             "billInfo": []
        #         }),)

        # if not auth[0]['journal_id']:
        #     return  werkzeug.wrappers.Response(
        #             status=400,
        #             content_type="application/json; charset=utf-8",
        #             response=json.dumps(
        #                 {
        #                     "requestId": request_id,
        #                     "schemaVersion": "1.0",
        #                     "responseHeader":
        #                         {
        #                             "timestamp": timestamp,
        #                             "resultCode": "400",
        #                             "resultMessage": "There's an error from our side."
        #                         },
        #                     "billInfo": []
        #                     }),
        #     )

        # result = {
        #     "requestId": request_id,
        #     "schemaVersion": "1.0",
        #     "responseHeader": {
        #         "timestamp": timestamp,
        #         "resultCode": "0",
        #         "resultMessage": "SUCCESS"
        #     },
        #     "billInfo": [
        #         {
        #             "billId": customer_ref,
        #             "billTo": tenant_id.name,
        #             "billAmount": tenant_id.credit,
        #             "billCurrency": "USD",
        #             "billNumber": customer_ref,
        #             "dueDate": str(datetime.now()),
        #             "status": "PENDING",
        #             "partialPayAllowed": "1",
        #             "description": "BillType:Utility Bill"
        #         }
        #     ],
        #     "PayInfo": None
        # }

        # payment_id = request.env['mgs.payment.transaction'].sudo().create({
        #     'name':request_data['requestBody']['transacionInfo']['tansactionId'],
        #     'partner_id': tenant_id.id if tenant_id else None,
        #     'amount': request_data['requestBody']['transacionInfo']['amount'],
        #     'description': request_data['requestBody']['billInfo']['description'],
        #     'is_prepaid': request_data['requestBody']['billInfo']['isPrepaid'],
        #     'bill_to': request_data['requestBody']['billInfo']['billTo'],
        #     'paid_by': request_data['requestBody']['billInfo']['paidBy'],
        #     'ref': request_data['requestBody']['billInfo']['invoiceId'],
        #     'date': date.today(),
        #     'method_id': payment_method.id,
        #     'journal_id': auth[0]['journal_id'][0]
        # })

        # # payment_id.sudo().action_post()

        # result = {
        #     "requestId": request_id,
        #     "schemaVersion": "1.0",
        #     "responseHeader": {
        #         "timestamp": timestamp,
        #         "resultCode": "0",
        #         "resultMessage": "SUCCESS"
        #     },
        #     "confirmationId": "GAR0001-'%s'" % datetime.now()  # PartnerTransferid
        # }

        # return werkzeug.wrappers.Response(
        #     status=200,
        #     headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
        #     content_type="application/json; charset=utf-8",
        #     response=json.dumps(result),
        # )
