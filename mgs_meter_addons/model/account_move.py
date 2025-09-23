from odoo import models, fields, api


class Mgs_Account_Move_Extension(models.Model):
    _inherit = 'account.move'
    
    meter_serial_id = fields.Many2one(comodel_name="mgs_billing.meter", compute="_get_meter_id", store=True)
    
    
    @api.depends('reading_id')
    def _get_meter_id(self):
        for rec in self:
            rec.meter_serial_id = rec.reading_id.property_id.meter_serial_id.id
    
    
    