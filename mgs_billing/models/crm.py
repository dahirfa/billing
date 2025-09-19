# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    billing_customer_id = fields.Many2one('mgs_billing.billing_customer', string="Billing Customer")

    zone_id = fields.Many2one('mgs_billing.zone', string='Zone', tracking=True)

    property_id = fields.Many2one('mgs_billing.property', string='Property', tracking=True)

    property_type_id = fields.Many2one('mgs_billing.property.type', string='Property Type', ondelete='restrict', tracking=True)
    
    mobile = fields.Char(string="Tenant's Mobile")
    
    hide_create_customer_btn = fields.Boolean(default=False, compute='_compute_hide_create_customer_btn')
    

    @api.depends('partner_id', 'property_id')
    def _compute_hide_create_customer_btn(self):
        for r in self:
            r.hide_create_customer_btn = False
            if r.partner_id and r.property_id:
                r.hide_create_customer_btn = True

