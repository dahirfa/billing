# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MgsIntegrationLog(models.Model):
    _name = "mgs.integration.log"
    _description = "MGS Integration Log"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    

    name = fields.Char(
        string="Reference", required=True, default=lambda self: _("New"), copy=False
    )

    date = fields.Datetime(
        string="Date",
        default=fields.Datetime.now,
    )

    end_point = fields.Char(string="End Point")

    request_type = fields.Selection(
        [
            ("get", "GET"),
            ("post", "POST"),
            ("put", "PUT"),
            ("delete", "DELETE"),
            ("patch", "PATCH"),
            ("head", "HEAD"),
            ("options", "OPTIONS"),
            ("trace", "TRACE"),
            ("connect", "CONNECT"),
            ("other", "Other"),
        ],
        string="Request Type",
    )

    request_ip = fields.Char(
        string="Request IP",
    )

    error_message = fields.Html(
        string="Error Message",
    )

    @api.model
    def create(self, values):
        if values.get("name", _("New")) == _("New"):
            values["name"] = self.env["ir.sequence"].next_by_code(
                "mgs.integration.log"
            ) or _("New")

        result = super(MgsIntegrationLog, self).create(values)

        return result
