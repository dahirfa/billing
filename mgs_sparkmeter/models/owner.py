
from odoo import models, fields

class MGSBillingOwner(models.Model):
    _inherit = 'mgs_billing.billing_customer'

    def write(self, vals):
        res = super(MGSBillingOwner, self).write(vals)
        if vals.get('name', False):
            self.property_ids.filtered(lambda p: p.meter_type == 'smart' and p.property_sparkmeter_customer_id).action_update_sparkmeter_customer()
        return res