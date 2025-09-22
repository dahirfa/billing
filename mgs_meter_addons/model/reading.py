from odoo import models, fields, api


class Mgs_Reading_Extension(models.Model):
    _inherit = 'mgs_billing.reading'
    
    meter_serial_id = fields.Many2one(related='property_id.meter_serial_id')
    
    
    
    
class Mgs_Billing_Reading_Extension(models.Model):
    _inherit = 'mgs_billing.meter.reading'
    
    meter_serial_id = fields.Many2one(related='property_id.meter_serial_id')   
    
    
    
    
    
    
    
    
    
    