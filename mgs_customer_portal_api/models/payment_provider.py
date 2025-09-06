from odoo import _, api, fields, models


class PaymentProviderInherit(models.Model):
    _inherit = 'payment.provider'
    
    available_on_mobile_app = fields.Boolean(
        string='Available On Mobile App',
    )
    
    
