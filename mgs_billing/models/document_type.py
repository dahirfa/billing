# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MGSBillingDocType(models.Model):
    _name = 'mgs_billing.document_type'
    _description = 'MGS Billing Document Type'
    _order="id DESC"
    
    name = fields.Char('Name', required=True)
    active = fields.Boolean(default=True)
