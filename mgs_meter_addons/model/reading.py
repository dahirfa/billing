from odoo import models, fields, api


class Mgs_Reading_Extension(models.Model):
    _inherit = 'mgs_billing.reading'
    
    meter_serial_id = fields.Many2one(comodel_name="mgs_billing.meter", compute="_get_meter_id", store=True)
    
    
    @api.depends('property_id')
    def _get_meter_id(self):
        for rec in self:
            rec.meter_serial_id = rec.property_id.meter_serial_id.id
    
    
    
    
class Mgs_Billing_Reading_Extension(models.Model):
    _inherit = 'mgs_billing.meter.reading'
    
    meter_serial_id = fields.Many2one(comodel_name="mgs_billing.meter", compute="_get_meter_id", store=True)   
 
    @api.depends('property_id')
    def _get_meter_id(self):
        for rec in self:
            rec.meter_serial_id = rec.property_id.meter_serial_id.id
    
    
    
    
    
    