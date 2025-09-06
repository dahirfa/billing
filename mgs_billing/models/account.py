
from odoo import models, fields

from odoo.exceptions import  UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    reading_id = fields.Many2one('mgs_billing.reading', string='Meter Reading')

    def button_draft(self):
        for r in self:
            if r.reading_id and 'allow_action' not in self.env.context:
                raise UserError("Billing Invoices can be modified from the 'Utility' reading module only!")
        return super(AccountMove, self).button_draft()

    def button_cancel(self):
        for r in self:
            if r.reading_id and 'allow_action' not in self.env.context:
                raise UserError("Billing Invoices can be modified from the 'Utility' reading module only!")
        return super(AccountMove, self).button_cancel()

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for r in self:
            if r.reading_id and 'allow_action' not in self.env.context:
                raise UserError("Billing Invoices can be modified from the 'Utility' reading module only!")
        return res
