from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons.phone_validation.tools import phone_validation


class ResPartner(models.Model):
    _inherit = "res.partner"

    alternative_number = fields.Char(
        "Alternative Number",
        tracking=True,
        help="Alternative Number used for mobile app payment. This will be updated with the latest number the client use for payment",
    )

    
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

    


class PaymentTransaction(models.Model):
    _inherit = "mgs.payment.transaction"

    @api.model
    def create(self, values):
        result = super(PaymentTransaction, self).create(values)

        for rec in result:
            if rec.partner_id:
                if rec.paid_by and rec.paid_by.isdigit():
                    rec.partner_id.write({"alternative_number": rec.paid_by})

        return result





class MgsbillingPartner(models.Model):
    _inherit = 'mgs_billing.partner'
    
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

    
