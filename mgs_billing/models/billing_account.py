# -*- coding: utf-8 -*-

from odoo import models, fields, api
from statistics import mean
from odoo.exceptions import ValidationError
from lxml import etree


class ResPartner(models.Model):
    _inherit = 'res.partner'

    
    # @api.model
    # def get_view(self, view_id=None, view_type="form", toolbar=False, submenu=False):
    #     res = super().get_view(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_type == "form":
    #         doc = etree.XML(res['arch'])
    #         if self._context.get('default_is_tenancy'):
    #             for node in doc.xpath("//field[@name='mobile']"):
    #                 node.set('string', "Tenant's Mobile")
    #             for node in doc.xpath("//field[@name='phone']"):
    #                 node.set('string', "Owner's Phone")
    #         res['arch'] = etree.tostring(doc, encoding='unicode')
    #     return res


    @api.model
    def _mgs_credit_search(self, operator, operand):
        return self._asset_difference_search('asset_receivable', operator, operand)
    
    @api.model
    def _mgs_debit_search(self, operator, operand):
        return self._asset_difference_search('liability_payable', operator, operand)

    is_tenancy = fields.Boolean(default=False)

    is_collector = fields.Boolean(default=False)
    
    is_shareholder = fields.Boolean(default=False, string="Shareholder?", store=True)
    
    product_id = fields.Many2one('product.product', string="Plan", domain=[('is_billing_pan', '=', True)])
         
    billing_customer_id = fields.Many2one('mgs_billing.billing_customer', string="Billing Customer", ondelete='restrict')
    
    property_id = fields.Many2one('mgs_billing.property', string="Property", ondelete='restrict')
    
    zone_id = fields.Many2one('mgs_billing.zone', related='property_id.zone_id', store=True)
    
    average_usage = fields.Float('Average Usage', compute='_compute_average_usage')
    
    
    mgs_credit = fields.Monetary(compute='_mgs_credit_debit_get', search=_mgs_credit_search,
        string='Total Receivable', help="Total amount this customer owes you.",
        groups='account.group_account_invoice,account.group_account_readonly')
    
    
    mgs_debit = fields.Monetary(
        compute='_mgs_credit_debit_get', search=_mgs_debit_search, string='Total Payable',
        help="Total amount you have to pay to this vendor.",
        groups='account.group_account_invoice,account.group_account_readonly')
    
    
    mgs_total_due = fields.Monetary(
        compute='_mgs_credit_debit_get', string='Total Due',
        help="Total amount due",
        groups='account.group_account_invoice,account.group_account_readonly')
    
    
    alternative_number = fields.Char(
        "Sender's Number",
        tracking=True,
        help="Alternative Number used for mobile app payment. This will be updated with the latest number the client use for payment",
    )

    reading_history_counter = fields.Integer(string='Reading History', compute='compute_counter')
    
    payment_counter = fields.Integer(string='Customer Payments', compute='compute_counter')
    
    
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.property_id:
                name = " | ".join((name, record.property_id.name))
            result.append((record.id, name))
        return result
    
    
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
                raise ValidationError("This property has an active billing account!.")
                
    
    def get_partner_balance(self, account_type, id, debit_credit):
        partner_balance = """
                            select COALESCE(sum(%s""" % debit_credit + """), 0)
                            from account_move_line as aml
                            left join account_account as aa on aml.account_id=aa.id
                            where aml.partner_id = %s""" % str(id) + """
                            and aa.account_type in %s""" % account_type + """
                            and parent_state in ('posted')"""
        self.env.cr.execute(partner_balance)
        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    @api.depends_context('company')
    def _mgs_credit_debit_get(self):
        if not self.ids:
            self.mgs_debit = False
            self.mgs_credit = False
            return
        for r in self:
            r.mgs_debit = r.get_partner_balance("('liability_payable')", r.id, 'aml.credit - aml.debit')
            r.mgs_credit = r.get_partner_balance("('asset_receivable')", r.id, 'aml.debit - aml.credit')
            r.mgs_total_due = r.get_partner_balance("('liability_payable', 'asset_receivable')", r.id, 'aml.debit - aml.credit')

    @api.depends('property_id.meter_reading_ids', 'property_id.meter_reading_ids.reading_difference')
    def _compute_average_usage(self):
        for r in self:
            differences = r.property_id.meter_reading_ids.filtered(lambda x: x.state == 'posted' and x.billing_account_id.id == r.id).mapped('reading_difference')
            r.average_usage = mean(differences) if differences else 0.0


    @api.onchange('is_tenancy', 'billing_customer_id')
    def _onchange_tenancy(self):
        # for r in self:
        if self.is_tenancy and self.billing_customer_id:
            self.street = self.billing_customer_id.street
            self.mobile = self.billing_customer_id.mobile
            self.phone = self.billing_customer_id.phone
            self.zip = self.billing_customer_id.zip
            self.city = self.billing_customer_id.city
            self.state_id = self.billing_customer_id.state_id.id or None
            self.country_id = self.billing_customer_id.country_id.id or None


    @api.model
    def _mgs_credit_search(self, operator, operand):
        return self._asset_difference_search('asset_receivable', operator, operand)
    
    @api.model
    def _mgs_debit_search(self, operator, operand):
        return self._asset_difference_search('liability_payable', operator, operand)
    

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search((args + ['|', '|', '|', '|',
                                        ('name', 'ilike', name),
                                        ('mobile', 'ilike', name),
                                        ('phone', 'ilike', name),
                                        ('property_id.name', 'ilike', name),
                                        ('billing_customer_id.name', 'ilike', name)]), limit=limit)
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
    