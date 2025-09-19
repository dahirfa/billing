# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MgsProperty(models.Model):
    _inherit = 'mgs_billing.property'


    technician = fields.Char(string='Technician')
    ref_name = fields.Char('Reference Name')
    ref_mobile = fields.Char('Reference Mobile')
    
    
    extra_charge_invoice_ids = fields.Many2many('account.move', string='Invoices', copy=False, readonly=True)
    
    extra_charge_count = fields.Integer(string='Extra Charge Count', compute="_compute_extra_charge_count")
    old_house_no = fields.Char(string="Old House #", store=True)
    
    note = fields.Char('Note')


    pipe_extention = fields.Char(string='pipe extention')
    pipe_type = fields.Char(string='Pipe Type')
    meter_category = fields.Char(string='Meter Category')
    
    