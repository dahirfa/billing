# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class MGSBillingPartner(models.Model):
    _name = 'mgs_billing.partner'
    _description = 'MGS Billing Partner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id DESC"

    name = fields.Char('Name', required=True)
    image = fields.Binary(string="Image")
    mobile = fields.Char(string="Mobile", required=True)
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    document_type_id = fields.Many2one(
        'mgs_billing.document_type', string="Document Type")
    document_no = fields.Char(string="Document#")
    guarantor_id = fields.Many2one('mgs_billing.guarantor', string="Guarantor")
    remarks = fields.Char(string="Remarks")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)
    type = fields.Selection(
        [('owner', 'Owner'), ('tenant', 'Tenant')], default='owner')
    city = fields.Char(tracking=True)
    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)
    zip = fields.Char()
    country_id = fields.Many2one(
        'res.country', string='Country', ondelete='restrict', tracking=True)
    state_id = fields.Many2one(
        'res.country.state', string='Country', ondelete='restrict')
    partner_type = fields.Selection(
        [('individual', 'Individual'), ('company', 'Company')], default='individual')

    property_ids = fields.One2many(
        'mgs_billing.property', 'owner_id', string="Properties")
    active = fields.Boolean(
    default=True
    )
    def write(self, vals):
        res = super(MGSBillingPartner, self).write(vals)
        partner_obj = self.env['res.partner']
        domain = [('is_tenancy', '=', True),
                  ('customer_id', '=', self.id),
                  ('active', '=', True)]
        partner_id = partner_obj.search(domain, limit=1)
        if partner_id:
            name = None
            if self.id:
                name = self.name
            if partner_id.property_id:
                name += ' - ' + partner_id.property_id.name
            if not name:
                partner_id.billing_name = None
            else:
                partner_id.billing_name = name
            partner_obj.search(domain, limit=1).name = name
        return res

    # @api.onchange('name')
    # def onchange_name(self):
    #     partner_obj = self.env['res.partner']
    #     domain = [('is_tenancy', '=', True),
    #               ('customer_id', '=', self.id),
    #               ('active', '=', True)]
    #     partner_id = partner_obj.search(domain, limit=1)
    #     if partner_id:
    #         name = None
    #         if self.id:
    #             name = self.name
    #         if partner_id.property_id:
    #             name += ' - ' + partner_id.property_id.name
    #         if not name:
    #             partner_id.billing_name = None
    #         else:
    #             partner_id.billing_name = name
    #         partner_obj.search(domain, limit=1).update({
    #             'name': name
    #         })
    def unlink(self):
        reading_ids = self.env['mgs_billing.reading'].search(
            [('billing_account_id.customer_id', 'in', self.ids)])
        ba_ids = self.env['res.partner'].search(
            [('customer_id', 'in', self.ids)])
        if reading_ids or ba_ids:
            raise UserError(
                "You cannot delete partner which has reading history.")
        return super(MGSBillingPartner, self).unlink()
