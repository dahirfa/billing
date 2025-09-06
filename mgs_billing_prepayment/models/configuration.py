from odoo import models, fields


class ResCompanys(models.Model):
    _inherit = 'res.company'

    mgs_vat_tax_partner_id = fields.Many2one('res.partner', string='Default VAT Tax Partner')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mgs_vat_tax_partner_id = fields.Many2one('res.partner', string='Default VAT Tax Partner', related="company_id.mgs_vat_tax_partner_id", readonly=False)    