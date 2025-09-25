from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    team_id = fields.Many2one('helpdesk.team', string="Helpdesk Team", help="Default Team for CRM Ticket")
    
    
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    team_id = fields.Many2one('helpdesk.team', readonly=False, related='company_id.team_id',)
    
    
    
    