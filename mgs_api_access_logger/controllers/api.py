# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import requests
import werkzeug.wrappers as wrappers
import logging
import json
import urllib.parse
from psycopg2 import sql

_logger = logging.getLogger(__name__)


class ZkAttendence(http.Controller):

    @http.route("/device/info/", type="json", auth='user', methods=["POST"], csrf=False)
    def device_info(self, **kw):
        required_fields = ["username", "device_name", "device_version", "url_endpoint", "mac_address", "android_version", "operating_system", "app_version"]
        missing_fields = [field for field in required_fields if not kw.get(field)]
        _logger.info(missing_fields)
        if missing_fields:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }
            
            
        device_info_data = {
            "username": kw.get("username"),
            "device_name": kw.get("device_name"),
            "device_version": kw.get("device_version"),
            "ip_address":request.httprequest.remote_addr,
            "url_endpoint":kw.get("url_endpoint"),
            "mac_address": kw.get("mac_address"),
            "android_version": kw.get("android_version"),
            "operating_system": kw.get("operating_system"),
            "app_version": kw.get("app_version"),
        }
        device_info = request.env["mgs.device.info"].sudo().create(device_info_data)

        # Respond with success message
        return {
            "status": "success",
            "message": "Device info created successfully",
            "device_info_id": device_info.id,
        }
