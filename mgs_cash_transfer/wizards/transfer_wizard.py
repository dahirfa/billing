from odoo import models, fields, api

class TransferWizard(models.TransientModel):
    _name = 'mgs_cash_transfer.wizard'
    _description = 'Transfer Wizard'

    date_from = fields.Date(string="Start Date", default=fields.Date.context_today)
    date_to = fields.Date(string="End Date", default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', string="Journal", domain=[('type', 'in', ['cash', 'bank'])])
    

    def print_report(self):
        datas = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'journal_id': self.journal_id.id if self.journal_id else False,
        }
        return self.env.ref('mgs_cash_transfer.action_report_transfer').report_action(self, data=datas)
