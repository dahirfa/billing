# -*- coding: utf-8 -*-

from odoo import models, fields, api
from statistics import mean
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # name            = fields.Char       (index=True, default='/')
    is_tenancy = fields.Boolean(default=False)

    is_collector = fields.Boolean(default=False)
    date = fields.Date('Date', default=lambda self: fields.Date.today())
    product_id = fields.Many2one('product.product', string="Plan", domain=[('is_billing_pan', '=', True)])
    # owner_id = fields.Many2one('mgs_billing.partner', string="Owner", store=True, readonly=True, compute='_get_owner')
    customer_id = fields.Many2one(
        'mgs_billing.partner', string="Billing Customer", ondelete='restrict')
    property_id = fields.Many2one(
        'mgs_billing.property', string="Property", ondelete='restrict')
    mgs_ref = fields.Char(string='Ref')
    average_usage = fields.Float(
        'Average Usage', compute='_compute_average_usage')
    mgs_state = fields.Selection(
        [('active', 'Active'), ('close', 'Closed')], default='active')
    billing_name = fields.Char(string='Billing Name', compute='_compute_billing_name', store=True)

    @api.constrains('property_id')
    def _check_property_id(self):
        for record in self:
            if self.search_count([('active', '=', True), ('property_id.id', '=', record.property_id.id)]) > 1:
                raise ValidationError(
                    "This property has an active billing account!.")

    @api.onchange('property_id')
    def _onchange_property_id(self):
        if self.property_id:
            self.property_product_pricelist = self.property_id.property_type_id.pricelist_id
            self.product_id = self.property_id.product_id.id
            self.category_id = None
            self.category_id = [(4,self.property_id.zone_id.partner_category_id.id)]

    @api.onchange('billing_name')
    def _onchange_billing_name(self):
        if self.billing_name:
            self.name = self.billing_name

    # @api.depends('property_id')
    # def _get_owner(self):
    #     for record in self:
    #         if record.property_id and record.property_id.owner_id:
    #             record.customer_id = record.property_id.owner_id.id
    #         else:
    #             record.owner_id = None

    @api.depends('property_id', 'customer_id')
    def _compute_billing_name(self):
        for record in self:
            name = None
            if record.customer_id:
                name = record.customer_id.name
            if record.property_id:
                name += ' - ' + record.property_id.name
            if not name:
                record.billing_name = None
            else:
                record.billing_name = name

    @api.depends('property_id.meter_reading_ids', 'property_id.meter_reading_ids.reading_difference')
    def _compute_average_usage(self):
        for r in self:
            differences = r.property_id.meter_reading_ids.filtered(
                lambda x: x.state == 'posted' and x.billing_account_id.id == r.id).mapped('reading_difference')
            r.average_usage = mean(differences) if differences else 0.0

    @api.onchange('is_tenancy', 'customer_id')
    def _onchange_tenancy(self):
        # for r in self:
        if self.is_tenancy and self.customer_id:
            self.street = self.customer_id.street
            self.mobile = self.customer_id.mobile
            self.phone = self.customer_id.phone
            self.zip = self.customer_id.zip
            self.city = self.customer_id.city
            self.state_id = self.customer_id.state_id.id or None
            self.country_id = self.customer_id.country_id.id or None

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            # if record.property_id:
                # name = record.property_id.name
            if record.property_id:
                name = " | ".join((name, record.property_id.name))
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search((args + ['|', '|', '|',
                                        ('name', 'ilike', name),
                                        ('mobile', 'ilike', name),
                                        ('property_id.name', 'ilike', name),
                                        ('customer_id.name', 'ilike', name)]), limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()




    def generate_owners(self, batch_size=80):
        billing_customer_obj= self.env['mgs_billing.partner']
        accounts= self.filtered(lambda x: x.is_tenancy== True and not x.customer_id)
        try:
            for r in accounts:
                string = r.name
                mobile = r.mobile.replace(' ', '').replace('+', '') if r.mobile else None
                index = string.find(' - ')
                name = string[:index].strip()
                property_id= r.property_id
                billing_customer = billing_customer_obj.search([('name','=',name),('mobile','=',mobile)],limit=1)
                if billing_customer:
                    r.customer_id = billing_customer.id
                    property_id.write({'owner_id':billing_customer.id})
                    continue
                else:
                    phone  = r.phone.replace(' ', '').replace('+', '') if r.phone else None
                    new_customer = billing_customer_obj.create({'name':name, 'mobile':mobile,'phone':phone, 'street':r.street,'type':'owner'})
                    r.customer_id = new_customer.id
                    property_id.write({'owner_id':new_customer.id})
            # accounts.action_cancel()
            # accounts.action_draft()
            # accounts.action_confirm()
        except Exception as error:
            self.env.cr.rollback()
            raise error
        else:
            self.env.cr.commit()
        # if accounts:
        #     self.env['mgs_billing.reading'].fix_invoices(batch_size)
