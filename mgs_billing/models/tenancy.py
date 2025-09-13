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
    property_id = fields.Many2one('mgs_billing.property', string="Property", ondelete='restrict')
    zone_id = fields.Many2one('mgs_billing.zone', related='property_id.zone_id', store=True)
    
    mgs_ref = fields.Char(string='Ref')
    average_usage = fields.Float(
        'Average Usage', compute='_compute_average_usage')
    mgs_state = fields.Selection(
        [('active', 'Active'), ('close', 'Closed')], default='active')
    billing_name = fields.Char(string='Billing Name', compute='_compute_billing_name', store=True)
    
    alternative_number = fields.Char(
        "Sender's Number",
        tracking=True,
        help="Alternative Number used for mobile app payment. This will be updated with the latest number the client use for payment",
    )

    reading_history_counter = fields.Integer(string='Reading History', compute='compute_counter')
    
    payment_counter = fields.Integer(string='Customer Payments', compute='compute_counter')
    
    @api.constrains("mobile", "country_id")
    def _check_mobile_number(self):
        for record in self:
            if record.mobile:
                # Step 1: Remove '+' if present
                mobile_number = record.mobile.replace("+", "").replace(" ", "")

                # Step 2: Determine the country_id
                country = record.country_id or self.env.company.country_id

                if country and country.phone_code:
                    # Step 3: Remove the country calling code if present
                    phone_code = str(country.phone_code)
                    if mobile_number.startswith(phone_code):
                        mobile_number = mobile_number[len(phone_code) :]

                # Step 4: Validate the length of the remaining number
                if len(mobile_number) != 9:
                    raise ValidationError(
                        "The mobile number must have exactly 9 digits after the country code."
                    )

    @api.constrains("phone", "country_id")
    def _check_phone_number(self):
        for record in self:
            if record.phone:
                # Step 1: Remove '+' if present
                phone_number = record.phone.replace("+", "").replace(" ", "")

                # Step 2: Determine the country_id
                country = record.country_id or self.env.company.country_id

                if country and country.phone_code:
                    # Step 3: Remove the country calling code if present
                    phone_code = str(country.phone_code)
                    if phone_number.startswith(phone_code):
                        phone_number = phone_number[len(phone_code) :]

                # Step 4: Validate the length of the remaining number
                if len(phone_number) != 9:
                    raise ValidationError(
                        "The phone number must have exactly 9 digits after the country code."
                    )


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


    def compute_counter(self):
        for r in self:
            r.reading_history_counter = len(r.property_id.meter_reading_ids)
            r.payment_counter = self.env['account.payment'].search_count([('partner_id.id','=',r.id)])

    
    def view_readings(self):
        return {
            'name': 'Readings',
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list',
            'res_model': 'mgs_billing.reading',
            'domain': [('property_id', 'in', self.property_id.ids)],
            'context': {"create":False, 'search_default_posted': 1}
        }

    def action_open_reading_history(self):
        self.ensure_one()
        action = self.env.ref('mgs_billing.mgs_billing_meter_reading_action').sudo().read()[0]
        action['domain'] = "[('property_id.id','=',%s)]" % str(self.property_id.id)
        action['context'] = {}
        action['context']['create'] = False
        return action
    
    
    def action_open_customer_payment(self):
        self.ensure_one()
        action = self.env.ref('account.action_account_payments').sudo().read()[0]
        action['domain'] = "[('partner_id.id','=',%s)]" % str(self.id)
        action['context'] = {"default_partner_id": self.id}
        # action['context']['create'] = False
        return action
    