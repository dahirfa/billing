# -- coding: utf-8 --

from odoo import models, fields, api


class MgsBillingProperty(models.Model):
    _inherit = 'mgs_billing.property'
    
    auto_reset  = fields.Boolean(default=False)
    
    
    def action_create_sparkmeter_customer(self, meter_id):
        res = super(MgsBillingProperty, self).action_create_sparkmeter_customer(meter_id)
        if res == 201:
            self.auto_reset = True
        return res