# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MGSBillingOwner(models.Model):
    _name = 'mgs_billing.owner'
    _description = 'MGS Billing Owner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order="id DESC"

    name = fields.Char('Name', required=True)
    mobile = fields.Char(string="Tenant's Mobile", required=True)
    phone = fields.Char(string="Owner's Phone")
    email = fields.Char(string="Email")
    document_type_id = fields.Many2one('mgs_billing.document_type', string="Document Type")
    document_no = fields.Char(string="Document#")
    # guarantor_id = fields.Many2one('mgs_billing.guarantor', string="Guarantor")
    remarks = fields.Char(string="Remarks")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    
    city = fields.Char(tracking=True)
    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)
    zip = fields.Char()
    country_id = fields.Many2one('res.country',string='Country', ondelete='restrict',tracking=True)
    state_id = fields.Many2one('res.country.state',string='Country', ondelete='restrict')
    
    owner_type = fields.Selection([('individual', 'Individual'), ('company', 'Company')])
