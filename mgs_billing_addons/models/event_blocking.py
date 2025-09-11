
from odoo import models, fields, api


class AccountMove(models.Model):
    _name = 'mgs.meter.event.blocking'
    _description = 'Meter Event Blocking'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    
    property_id = fields.Many2one(string="Property", comodel_name="mgs_billing.property")
    date = fields.Date(string="Date", default=fields.Date.today())
    reason = fields.Char(string="Reason")
    user_id = fields.Many2one(string="Registered Collector", comodel_name="res.users")
    