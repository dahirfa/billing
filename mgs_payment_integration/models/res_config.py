from odoo import models, fields


class ResCompanys(models.Model):
    _inherit = 'res.company'

    mgs_bank_suspense_id = fields.Many2one('account.account', string='Bank Suspense account')
    mgs_unknown_partner_id = fields.Many2one('res.partner', string='Default Unknown Partner', domain=[('active','=',False)])
    
    
    mgs_email_to_notify = fields.Char(string='Email to notify')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mgs_bank_suspense_id = fields.Many2one('account.account', string='Bank Suspense account', related="company_id.mgs_bank_suspense_id", readonly=False)
    mgs_unknown_partner_id = fields.Many2one('res.partner', string='Default Unknown Partner', related="company_id.mgs_unknown_partner_id", readonly=False, domain=[('active','=',False)])
    
    mgs_email_to_notify = fields.Char(string='Email to notify', related="company_id.mgs_email_to_notify", readonly=False)
    