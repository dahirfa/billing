# -*- coding: utf-8 -*-

from odoo import models, fields, api
import pytz


class MgsDevice(models.Model):
    _name = "mgs.device.info"
    _description = "Device Info"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    username = fields.Char(tracking=1)
    device_name = fields.Char(tracking=1)
    device_version = fields.Char(tracking=1)
    mac_address = fields.Char(tracking=1)
    ip_address = fields.Char(tracking=1)
    url_endpoint = fields.Char(tracking=1)
    android_version = fields.Char(tracking=1)
    operating_system = fields.Char(tracking=1)
    app_version = fields.Char(tracking=1)
