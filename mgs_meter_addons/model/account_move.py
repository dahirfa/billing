from odoo import models, fields, api


class Mgs_Account_Move_Extension(models.Model):
    _inherit = 'account.move'
    
    meter_serial_id = fields.Many2one(related='reading_id.property_id.meter_serial_id')