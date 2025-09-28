from odoo import models, fields, api

class PaymentCancellationWizard(models.TransientModel):
    _name = 'mgs_payment_integration.payment_cancellation'
    _description = 'Payment Cancellation Report Wizard'

    date_from = fields.Date(string="Start Date", default=fields.Date.context_today)
    date_to = fields.Date(string="End Date", default=fields.Date.context_today)
    partner_id = fields.Many2one('res.partner', string="Customer")

    def print_report(self):
      
        datas = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'partner_id': self.partner_id.id if self.partner_id else False,
        }
        return self.env.ref('mgs_payment_integration.action_report_payment_cancellation').report_action(self, data=datas)