from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    mgs_payroll_account_exp = fields.Many2many('hr.salary.rule',string='Account Export Template')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    mgs_payroll_account_exp  = fields.Many2many('hr.salary.rule',string='Account Export Template',  related="company_id.mgs_payroll_account_exp", readonly=False)
