# -*- coding: utf-8 -*-
from odoo import http
import json
from datetime import datetime, date
from odoo.http import request
import werkzeug.wrappers
import logging
import requests
from requests.exceptions import ConnectionError, HTTPError
import pytz
_logger = logging.getLogger(__name__)


class MGSWaafiPayIntegrationPayBill(http.Controller):

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

    # Pay Bill
    @http.route(
        "/api/waafipay/paybill",
        methods=["GET", "POST"],
        type="json",
        auth="user",
        csrf=False,
    )
    def paybill(self, **kw):

        partner_id = kw.get("partner_id")
        user_partner = (
            request.env["res.users"]
            .search([("id", "=", request.session.uid)], limit=1)
            .commercial_partner_id.id
        )
        if (
            partner_id != user_partner
            and self.check_reading_access(user_partner, partner_id) == False
        ):
            return {
                "statuscode": 401,
                "statuscode": "You are not authorized to create this document.",
            }
        if not kw.get("partner_id", False):
            return {
                "statuscode": 400,
                "statusmessage": "You are not authorized to create this document.",
            }

        provider_id = (
            request.env["payment.provider"]
            .sudo()
            .search([("code", "=", "waafipay")], limit=1)
        )
        payment_method = request.env.ref(
            "mgs_waafipay_intergration.payment_method_waafipay"
        )
        payment_provider = payment_method.sudo()
        waafi_url = "https://api.waafipay.net/asm"

        merchant_uid = provider_id.merchant_uid
        api_userid = provider_id.api_userid
        api_key = provider_id.api_key

        request_data = {
            "providor_id": kw.get("providor_id"),
            "partner_id": partner_id,
            "amount": kw.get("amount"),
            "sender_number": kw.get("sender_number"),
            "description": kw.get("description"),
        }


        if float(request_data["amount"]) <= 0.0:
            return {
                'statuscode': 400,
                "statusmessage": "Amount can not be negative or zero",
            }

        partner = (
            request.env["res.partner"]
            .sudo()
            .search([("id", "=", request_data["partner_id"])])
        )
        payload = json.dumps(
            {
                "schemaVersion": "1.0",
                "requestId": f"NECSOM-{datetime.now()}",
                "timestamp": datetime.now(),
                "channelName": "WEB",
                "serviceName": "API_PURCHASE",
                "serviceParams": {
                    "merchantUid": merchant_uid,
                    "apiUserId": api_userid,
                    "apiKey": api_key,
                    "paymentMethod": "MWALLET_ACCOUNT",
                    "payerInfo": {"accountNo": request_data["sender_number"]},
                    "transactionInfo": {
                        "referenceId": f"{partner.id}",
                        "invoiceId": f"{partner.id} - {partner.name}",
                        "amount": request_data["amount"],
                        "currency": "USD",
                        "description": f"{request_data['description']}",
                        "paymentBrand": "SAHAL",
                    },
                },
            },
            indent=4,
            sort_keys=True,
            default=str,
        )

        try:
            _logger.info(f"Sending Request to {waafi_url}")
            _logger.info(f"Sending Request to {payload}")
            response = requests.post(
                waafi_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                timeout=80,
            )
        except (ConnectionError, HTTPError):

            values = {
                "date": datetime.now(),
                "end_point": response.url,
                "request_type": "post",
                "request_ip": request.httprequest.remote_addr,
                "error_message": f"{ConnectionError} \n{HTTPError}",
            }
            error_log = (
                request.env["mgs.integration.log"].sudo().create(values)
            )  # Log Errors

            return {
                "statuscode": 502,
                "connection_error": ConnectionError,
                "http_error": HTTPError,
                "error_refference": error_log.name,
            }

        if response:
            response_values = json.loads(response.text)
            if response_values["responseCode"] == "2001":  # 2001 is success
                try:
                    _logger.info(response_values)
                    waafi_date = datetime.strptime(response_values["timestamp"], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')
                    input_date = datetime.strptime(waafi_date, '%Y-%m-%d %H:%M:%S')
                    input_timezone = pytz.timezone('Africa/Mogadishu')
                    utc_date = input_timezone.localize(input_date).astimezone(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')

                    payment_id = (
                        request.env["mgs.payment.transaction"]
                        .sudo()
                        .create(
                            {
                                "name": response_values["params"]["transactionId"],
                                "partner_id": partner.id if partner else None,
                                "amount": float(request_data["amount"]),
                                "ref": response_values["params"]["transactionId"],
                                "date": utc_date, #TODO: CONVERT TO Africa/Mogadishu if NEEDED
                                "paid_by":request_data["sender_number"],
                                "method_id": provider_id.id,
                                "journal_id": provider_id.journal_id.id,
                            }
                        )
                    )

                    if payment_id.state == "duplicate":
                        payment_id.sudo().unlink()
                        return {
                            "statuscode": 400,
                            "statusmessage": "error - Duplicate Payment",
                        }
                    return {
                        "statuscode": 200,
                        "statusmessage": "success",
                        "transactionid": payment_id.id,
                    }
                    
                except Exception as e:
                    _logger.error(f"Error processing payment: {str(e)}")
                    
                    values = {
                    "date": datetime.now(),
                    "end_point": response.url,
                    "request_type": "post",
                    "request_ip": request.httprequest.remote_addr,
                    "error_message": f"{request_data} \n{str(e)}",
                    }
                    error_log = (
                        request.env["mgs.integration.log"].sudo().create(values)
                    )  # Log Errors
                    
                    return {
                        "statuscode": 500,
                        "statusmessage": f"Process Failed, Please raise a ticket or contact customer support for assistance",
                        "error_refference": error_log.name,
                    }
                    
            else:
                _logger.error(response_values)
                _logger.error(
                    "WaafiPay Transaction Failed with response : %s"
                    % str(response_values["responseMsg"])
                )
                values = {
                    "date": datetime.now(),
                    "end_point": response.url,
                    "request_type": "post",
                    "request_ip": request.httprequest.remote_addr,
                    "error_message": f"{request_data}-------{response_values['responseMsg']}--------{response_values}",
                }
                error_log = (
                    request.env["mgs.integration.log"].sudo().create(values)
                )  # Log Errors

                return {
                    "statuscode": 400,
                    "statusmessage": response_values["responseMsg"],
                    "error_refference": error_log.name,
                }
