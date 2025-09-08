# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TestImport(models.Model):
    _name = 'mgs_billing_addons.test_import'
    _description = 'Test Import'

    name = fields.Char(string='Name')
    mobile = fields.Char(string='Mobile')
    alternative_mobile = fields.Char(string='Alternative Mobile')
    email = fields.Char(string='Email')
    reference_name = fields.Char(string='Reference Name')
    reference_mobile = fields.Char(string='Reference Mobile')
    technician = fields.Char(string='Technician')
    wires = fields.Char(string='Wires')
    poles = fields.Char(string='Poles')
    meter_type = fields.Char(string='Type')
    bill_plan = fields.Char(string='BillPlan')
    discount_type = fields.Char(string='Discount Type')
    customer_type = fields.Char(string='Customer Type')
    connection_date = fields.Char(string='Connection Date')
    security_deposit = fields.Char(string='security_deposit')
    initital_meter_read = fields.Char(string='Initital Meter Read')
    total_receivable = fields.Char(string='Total Receivable')
    zone = fields.Char(string='Zone')
    transformer = fields.Char(string='Transformer')
    street = fields.Char(string='Street')
    area = fields.Char(string='Area')
    meter_number = fields.Char(string='Meter Number')
