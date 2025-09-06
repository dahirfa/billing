from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    draft_stage_id = fields.Many2one('helpdesk.stage', config_parameter='mgs_helpdesk_api.draft_stage_id')
    in_progress_stage_id = fields.Many2one('helpdesk.stage', config_parameter='mgs_helpdesk_api.in_progress_stage_id')
    done_stage_id = fields.Many2one('helpdesk.stage', config_parameter='mgs_helpdesk_api.done_stage_id')
    to_review_stage_id = fields.Many2one('helpdesk.stage', config_parameter='mgs_helpdesk_api.to_review_stage_id')
    cancel_stage_id = fields.Many2one('helpdesk.stage', config_parameter='mgs_helpdesk_api.cancel_stage_id')
    suspended_stage_id = fields.Many2one('helpdesk.stage', config_parameter='mgs_helpdesk_api.suspended_stage_id')

    @api.model
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('mgs_helpdesk_api.draft_stage_id',self.draft_stage_id.id)
        self.env['ir.config_parameter'].sudo().set_param('mgs_helpdesk_api.in_progress_stage_id',self.in_progress_stage_id.id)
        self.env['ir.config_parameter'].sudo().set_param('mgs_helpdesk_api.done_stage_id',self.done_stage_id.id)
        self.env['ir.config_parameter'].sudo().set_param('mgs_helpdesk_api.to_review_stage_id',self.to_review_stage_id.id)
        self.env['ir.config_parameter'].sudo().set_param('mgs_helpdesk_api.cancel_stage_id',self.cancel_stage_id.id)
        self.env['ir.config_parameter'].sudo().set_param('mgs_helpdesk_api.suspended_stage_id',self.suspended_stage_id.id)