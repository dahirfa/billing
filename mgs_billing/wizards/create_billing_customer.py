# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.addons.phone_validation.tools import phone_validation


class CreateCustomerWizard(models.TransientModel):
    _name = 'mgs_billing.customer.wizard'
    _description = 'Create Customer Wizard'

    # Owner form
    lead_id = fields.Many2one('crm.lead', string='Lead')
    name = fields.Char('Name', required=True)
    image = fields.Binary(string="Image")
    # Address
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Area')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    zone_id = fields.Many2one('mgs_billing.zone', string='Zone', required=True)
    city = fields.Char(string="City")

    partner_type = fields.Selection([('individual', 'Individual'), ('company', 'Company')], default='individual')
    
    product_id = fields.Many2one('product.product', string="Billing Plan", domain=[('is_billing_pan', '=', True)], required=True)
    
    mobile = fields.Char(string="Tenant's Mobile", required=True)
    
    phone = fields.Char(string="Owner's Phone")
    
    email = fields.Char(string="Email")

    existing_customer = fields.Boolean(default=False, string='Ma Customer Horay u Jiray baa?')
    
    billing_customer_id = fields.Many2one('mgs_billing.billing_customer', string="Merge with")

    document_type_id = fields.Many2one('mgs_billing.document_type', string="Document Type")
    
    document_no = fields.Char(string="Document#")

    ref_name = fields.Char('Reference Name')
    ref_mobile = fields.Char('Reference Mobile')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    # Propery form
    initial_meter = fields.Float(string='Initial Meter Read')
    property_type_id = fields.Many2one('mgs_billing.property.type', string='Type', required=True)
   
    customer_type = fields.Selection([('normal', 'Normal Customer'), ('free', 'Free Customer'),], default='normal', string='Customer Type')

    connection_date = fields.Datetime(string='Connection Date', default=fields.Datetime.now)
    


    @api.model
    def default_get(self, fields):
        rec = super(CreateCustomerWizard, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        lead_id = self.env[active_model].browse(active_ids)

        rec.update({
            'lead_id': lead_id.id,
            'name': lead_id.name,
            'mobile': lead_id.mobile,
            'phone': lead_id.phone,
            'zone_id': lead_id.zone_id.id,
            'street': lead_id.street,
            'email': lead_id.email_from,
            'company_id': lead_id.company_id.id,
            'country_id': self.env.company.country_id.id,
            'state_id': self.env.company.state_id.id,
            "city": self.env.company.city,
            'property_type_id': lead_id.property_type_id,
        })

        return rec
    
    
    
    @api.onchange('property_type_id')
    def _onchange_property_type_id(self):
        if self.property_type_id.product_id.id:
            self.product_id = self.property_type_id.product_id.id
        else:
            self.product_id = False
    
    
    def _check_phone_number(self, phone):
        billing_customer_id = self.billing_customer_id
        if phone:
            phone_number = phone.replace("+", "").replace(" ", "")
            country = billing_customer_id.country_id or self.env.company.country_id

            if country and country.phone_code:
                phone_code = str(country.phone_code)
                if phone_number.startswith(phone_code):
                    phone_number = phone_number[len(phone_code) :]

            return False if len(phone_number) != 9 else True
        return True
    
    
    def _check_mobile_number(self, mobile):
        billing_customer_id = self.billing_customer_id
        if mobile:
            mobile_number = mobile.replace("+", "").replace(" ", "")
            country = billing_customer_id.country_id or self.env.company.country_id

            if country and country.phone_code:
                phone_code = str(country.phone_code)
                if mobile_number.startswith(phone_code):
                    mobile_number = mobile_number[len(phone_code) :]

            return False if len(mobile_number) != 9 else True
        return True
    
    
    
    def _prepare_owner_vals(self):
        """Prepare values for creating owner"""
        return {
            'name': self.name,
            'mobile': self.mobile,
            'phone': self.phone,
            'email': self.email,
            'street': self.street,
            'street2': self.street2,
            'state_id': self.state_id.id,
            'country_id': self.country_id.id,
            'city': self.city,
            'company_id': self.company_id.id,
            'image': self.image,
        }
        
        
        
    def _prepare_property_vals(self, billing_customer_id):
        return {
            'zone_id': self.zone_id.id,
            'street': self.street,
            'street2': self.street2,
            'state_id': self.state_id.id,
            'country_id': self.country_id.id,
            'city': self.city,
            'customer_type': self.customer_type,
            'initial_meter': self.initial_meter,
            'billing_customer_id': billing_customer_id.id,
            'product_id': self.product_id.id,
            'property_type_id': self.property_type_id.id,
            'company_id': self.company_id.id,
            'connection_date': self.connection_date,
        }
    

    def action_proceed(self):
        owner_obj = self.env['mgs_billing.billing_customer']
        property_obj = self.env['mgs_billing.property']
        billing_customer_id = self.billing_customer_id

       
        if not billing_customer_id:
            billing_customer_id = owner_obj.create(self._prepare_owner_vals())

        
        if not self._check_phone_number(billing_customer_id.phone):
            raise ValidationError(
                "The phone number must have exactly 9 digits after the country code "
                "(+252907707070). Please fix the number of the contact you're merging with."
            )
        
        property_id = property_obj.create(self._prepare_property_vals(billing_customer_id))
        
        property_id.create_billing_account(partner_id=self.lead_id.partner_id.id if self.lead_id.partner_id else False)
       
        write_vals = {
            "property_id": property_id.id,
            "billing_customer_id": billing_customer_id.id,
        }

        if not self.lead_id.partner_id:
            write_vals["partner_id"] = property_id.billing_account_id.id

        self.lead_id.write(write_vals)

    
    
    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        if self.phone:
            self.phone = self._phone_format(self.phone, force_format='INTERNATIONAL')

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        if self.mobile:
            self.mobile = self._phone_format(self.mobile, force_format='INTERNATIONAL')

    def _phone_format(self, number, country=None, company=None, force_format='E164'):
        country = country or self.country_id or self.env.company.country_id
        if not country or not number:
            return number
        return phone_validation.phone_format(
            number,
            country.code if country else None,
            country.phone_code if country else None,
            force_format=force_format,
            raise_exception=False
        )
        
        
        
        
        
