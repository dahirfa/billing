# -*- coding: utf-8 -*-
from odoo import http
import json
from datetime import datetime, date
from odoo.http import request
import werkzeug.wrappers
import logging
import pytz
from odoo.exceptions import AccessDenied, AccessError


_logger = logging.getLogger(__name__)


class MgsPremierIntegration(http.Controller):

    def premier_authenticate(self, key, db):
        payment_method = request.env.ref(
            "mgs_premier_integration.payment_provider_premier"
        )
        user_id = payment_method.sudo().premier_user_id
        try:
            request.session.authenticate(db, user_id.login, key)
        except AccessError as aee:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"error_message": "Error: %s" % aee.name}),
            )
        except AccessDenied as ade:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"error_message": "Error: Access denied"}),
            )
        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps({"success_message": "Authenticated"}),
        )

    def create_log(self, end_point, request_type, request_ip, error_message):
        values = {
            "date": datetime.now(),
            "end_point": end_point,
            "request_type": request_type,
            "request_ip": request_ip,
            "error_message": error_message,
        }
        error_log = (
            request.env["mgs.integration.log"].sudo().create(values)
        )  # Log Errors

        return error_log

    # Bill

    @http.route(
        "/api/premier/property",
        methods=["GET", "POST"],
        type="http",
        auth="public",
        csrf=False,
    )
    def customer_balance_info(self, **kw):
        db = request._cr.dbname
        headers = request.httprequest.headers
        authenticate = self.premier_authenticate(headers.get("key"), db)
        """
        Body [meter_no]
        Header [key]
        """
        if authenticate.status_code != 200:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "statusmessage": "Authentication failed, Invalid credentials or revoked Access",
                    }
                ),
            )

        body = json.loads(request.httprequest.data)

        tenant_id = (
            request.env["res.partner"]
            .sudo()
            .search([("property_id.name", "=", body["meter_no"])], limit=1)
        )

        if not tenant_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"statusmessage": "Invalid Meter Number"}),
            )

        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            response=json.dumps(
                {
                    "meter_no": tenant_id.property_id.name,
                    "customer_name": tenant_id.name,
                    "balance": round(tenant_id.credit, 4),
                }
            ),
        )

    @http.route(
        "/api/premier/payment",
        methods=["GET", "POST"],
        type="http",
        auth="none",
        csrf=False,
    )
    def payment(self, **kw):
        db = request._cr.dbname
        headers = request.httprequest.headers
        authenticate = self.premier_authenticate(headers.get("key"), db)
        """
        Body [meter_no, amount_paid, date, transaction_id, sender_mobile]
        Header [key]
        """
        if authenticate.status_code != 200:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "error_message": "Authentication failed, Invalid credentials or revoked Access"
                    }
                ),
            )

        body = json.loads(request.httprequest.data)
        tenant_id = (
            request.env["res.partner"]
            .sudo()
            .search([("property_id.name", "=", body.get("meter_no"))], limit=1)
        )

        if not tenant_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "error_message": "Invalid meter number",
                    }
                ),
            )

        if float(body.get("amount_paid")) <= 0.0:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "error_message": "Amount can not be negative or zero",
                    }
                ),
            )

        payment_provider = request.env.ref(
            "mgs_premier_integration.payment_provider_premier"
        )

        if not payment_provider.sudo().journal_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                response=json.dumps({"error_message": "Can not complete this request"}),
            )

        input_date = datetime.strptime(body.get("date"), "%m-%d-%Y %H:%M:%S")
        input_timezone = pytz.timezone("Africa/Mogadishu")
        # Convert the input date to UTC timezone
        utc_date = input_timezone.localize(input_date).astimezone(pytz.UTC)

        try:
            payment_id = (
                request.env["mgs.payment.transaction"]
                .sudo()
                .create(
                    {
                        "name": body.get("transaction_id"),
                        "partner_id": tenant_id.id if tenant_id else None,
                        "amount": body.get("amount_paid"),
                        "paid_by": body.get("sender_mobile"),
                        "ref": body.get("transaction_id"),
                        "meter_no": body.get("meter_no"),
                        "date": utc_date.replace(tzinfo=None),
                        "method_id": payment_provider.id,
                        "journal_id": payment_provider.journal_id.id,
                    }
                )
            )

            if payment_id.state == "duplicate":
                _logger.error(
                    "---------------Premier Bank Transaction Failed (Duplicate Payment)---------------"
                )
                payment_id.sudo().unlink()
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps({"error_message": "Duplicate Payment"}),
                )

            _logger.info(
                "---------------Premier Bank Transaction Success---------------"
            )
            _logger.info(f"--------------------{payment_id.id}--------------------")
            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                response=json.dumps(
                    {
                        "success_message": "Transaction created successfully",
                        "necsom_transaction_id": payment_id.id,
                    }
                ),
            )

        except Exception as e:
            _logger.error(
                "---------------Premier Bank Transaction Failed---------------"
            )

            _logger.error(str(e))
            error_log = self.create_log(
                request.httprequest.url,
                str(request.httprequest.method).lower(),
                request.httprequest.remote_addr,
                str(e),
            )

            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                response=json.dumps(
                    {
                        "error_message": "Transaction Process Failed",
                        "error_reference": error_log.name,
                    }
                ),
            )
