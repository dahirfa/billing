from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError



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



    
