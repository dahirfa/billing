from odoo import models, fields, api


class MGSBillingMeter(models.Model):
    _name = 'mgs_billing.meter'
    _description = 'Meter'
    _order="id DESC"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    
    name        = fields.Char(string='Serial #', tracking=1, required=True)
    meterid     = fields.Char(string='ID', tracking=1)
    owner       = fields.Selection([('company', 'Owned by company'), ('third_party', 'Third Party')], tracking=1)
    company_id  = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, tracking=1)
    property_id = fields.Many2one('mgs_billing.property')
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'The name must be unique.'),
    ]