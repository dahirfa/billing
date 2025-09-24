
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




class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def calculate_percentage(self, amount, percentage):
        return amount * (percentage / 100)
    
    def action_post(self):
        res = super(AccountPayment, self).action_post()
        property_id = self.partner_id.property_id
        mgs_auto_reconnect_house = self.env.company.mgs_auto_reconnect_house
        
        if self.partner_id.is_tenancy == True and property_id and property_id.state == 'disconnected' and mgs_auto_reconnect_house:
            prev_bal = self.partner_id.mgs_credit
            if self.amount >= self.calculate_percentage(prev_bal, self.env.company.mgs_reconnection_percentage):
                self.partner_id.property_id.action_change_state(
                    'connected', 'Auto reconnect')
        return res