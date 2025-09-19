
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
    
    
    def get_mgs_partner_prev_balance(self, partner_id=None, date=fields.Date.today()):
        params = [str(partner_id), 'asset_receivable', date]
        query = """
                SELECT COALESCE(sum(debit - credit), 0)
                FROM account_move_line aml
                LEFT JOIN account_account as aa ON aml.account_id=aa.id
                WHERE aml.partner_id = %s
                AND aa.account_type = %s
                AND aml.date < %s
                AND parent_state = 'posted' """
        self.env.cr.execute(query, tuple(params))
        data = self.env.cr.fetchone() or 0.0
        return data[0]
