from odoo import models, fields


class ResCompanys(models.Model):
    _inherit = 'res.company'

    mgs_sahal_im_journal_id = fields.Many2one('account.journal', string='Import Journal (Sahal)')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mgs_sahal_im_journal_id = fields.Many2one('account.journal', string='Import Journal (Sahal)', related="company_id.mgs_sahal_im_journal_id", readonly=False)
    