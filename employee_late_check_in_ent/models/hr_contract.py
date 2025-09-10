from odoo import models, fields, _


class hr_contract_inherit(models.Model):
    _inherit = "hr.contract"

    late_penalty_id = fields.Many2one("latency.rule", domain="[('company_id','=',company_id)]", string="Late penalty type")



