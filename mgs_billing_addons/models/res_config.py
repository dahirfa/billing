# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = "res.company"

    mgs_auto_reconnect_house = fields.Boolean(default=False, string="Auto Reconnect")

    mgs_reconnection_percentage = fields.Float(string="Reconnection Percentage")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mgs_auto_reconnect_house = fields.Boolean(
        string="Auto Reconnect",
        related="company_id.mgs_auto_reconnect_house",
        readonly=False,
    )
    mgs_reconnection_percentage = fields.Float(
        related="company_id.mgs_reconnection_percentage",
        readonly=False,
        string="Reconnection Percentage",
    )
