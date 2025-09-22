from odoo import models, fields, api


class Mgs_Meter_Extension(models.Model):
    _inherit = 'mgs_billing.meter'
    
    meter_type = fields.Selection([('smart', 'Smart'), ('normal', 'Normal')], tracking=1, required=True, store=True, default='normal')