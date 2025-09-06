# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MGSBillingGuarantor(models.Model):
    _name = 'mgs_billing.guarantor'
    _description = 'MGS Billing Guarantor'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _order="id DESC"
    name = fields.Char('Name', required=True)
    mobile = fields.Char(string="Mobile")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    active = fields.Boolean(default=True)
