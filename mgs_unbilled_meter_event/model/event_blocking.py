
from odoo import models, fields, api


class Mgs_Meter_Event_Blocking(models.Model):
    _name = 'mgs.meter.event.blocking'
    _description = 'Unbilled Meter Event'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    
    property_id = fields.Many2one(string="Property", comodel_name="mgs_billing.property")
    zone_id = fields.Many2one(string="Zone", related="property_id.zone_id", comodel_name="mgs_billing.zone")
    date = fields.Date(string="Date", default=fields.Date.today())
    reason_id = fields.Many2one(string="Reason", comodel_name="mgs.meter.event.blocking.reason")
    user_id = fields.Many2one(string="Registered Collector", comodel_name="res.users")
    
    
    
class Mgs_Meter_Event_Blocking_Reasons(models.Model):
    _name = 'mgs.meter.event.blocking.reason'
    _description = 'Unbilled Meter Event Reason'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    
    name = fields.Char(string="Reason", ondelete="restrict")
       

    
    
    
    
    
    