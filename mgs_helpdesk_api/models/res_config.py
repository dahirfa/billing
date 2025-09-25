from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    draft_stage_id = fields.Many2one('helpdesk.stage', string="Draft Stage", help="Default stage for new tickets (Draft)",)
    in_progress_stage_id = fields.Many2one('helpdesk.stage', string="In Progress Stage", help="Stage for tickets being worked on",)
    done_stage_id = fields.Many2one('helpdesk.stage', string="Done Stage", help="Stage for completed tickets",)
    to_review_stage_id = fields.Many2one('helpdesk.stage', string="To Review Stage", help="Stage for tickets pending review",)
    cancel_stage_id = fields.Many2one('helpdesk.stage', string="Cancelled Stage", help="Stage for cancelled tickets",)
    suspended_stage_id = fields.Many2one('helpdesk.stage', string="Suspended Stage", help="Stage for suspended tickets",)
    team_id = fields.Many2one('helpdesk.team', string="Default Helpdesk Team", help="Default Team for Helpdesk Ticket")
    tag_id = fields.Many2one('helpdesk.tag', string="Default Tag", help="Default Tag for Helpdesk Ticket")
    
    

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    draft_stage_id = fields.Many2one('helpdesk.stage', readonly=False, related='company_id.draft_stage_id',)
    in_progress_stage_id = fields.Many2one('helpdesk.stage', readonly=False, related='company_id.in_progress_stage_id',)
    done_stage_id = fields.Many2one('helpdesk.stage', readonly=False, related='company_id.done_stage_id',)
    to_review_stage_id = fields.Many2one('helpdesk.stage', readonly=False, related='company_id.to_review_stage_id',)
    cancel_stage_id = fields.Many2one('helpdesk.stage', readonly=False, related='company_id.cancel_stage_id',)
    suspended_stage_id = fields.Many2one('helpdesk.stage', readonly=False, related='company_id.suspended_stage_id',)
    team_id = fields.Many2one('helpdesk.team', readonly=False, related='company_id.team_id',)
    tag_id = fields.Many2one('helpdesk.tag', readonly=False, related='company_id.tag_id',)
    
    
    
    
        
        
