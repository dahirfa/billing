# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = "crm.lead"

    pipe_extention = fields.Char(string="pipe extention")
    pipe_type = fields.Char(string="Pipe Type")
    meter_category = fields.Char(string="Meter Category")
    

   