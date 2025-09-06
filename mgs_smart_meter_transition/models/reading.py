# -- coding: utf-8 --

from odoo import models, fields
from odoo.exceptions import ValidationError

class MgsBillingReading(models.Model):
    _inherit = 'mgs_billing.reading'

    def action_confirm(self):
        res = super(MgsBillingReading, self).action_confirm()
        for r in self:
            if r.property_id.meter_type == 'smart' and r.property_id.auto_reset == True:
                try:
                    self.sudo()._action_reset_to_spark()
                except Exception as e:
                    r.property_id.sudo().write({'spark_remarks':'Reset Failed'})
                    r.property_id.sudo().message_post(body=f"Could not reset to smart meter reading - {e}")
        return res
    
    def _action_reset_to_spark(self):
        for r in self:
            property_id = r.property_id            
            latest_reading=property_id._get_last_spark_reading()
            if latest_reading['code']==200:
                amount =  latest_reading['data']
                reset_meter_record = self.env['mgs_billing.reset.meter'].sudo().create({
                    'property_id': property_id.id,
                    'reading': amount,
                    'date': fields.Date.today()
                })
                reset_meter_record.action_confirm()
                property_id.auto_reset = False
            else:
                self.env.cr.rollback()
                raise ValidationError("Could not reset to smart meter reading")