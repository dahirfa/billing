from odoo import models, fields, api


class Mgs_Property_Extension(models.Model):
    _inherit = 'mgs_billing.property'
    
    meter_serial_id = fields.Many2one(string="Meter", comodel_name="mgs_billing.meter", tracking=True)
    
    
    
    
    
    