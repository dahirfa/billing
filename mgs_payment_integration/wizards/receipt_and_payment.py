from odoo import models, fields, api
from odoo.exceptions import ValidationError
import xlsxwriter
import base64
from io import BytesIO


class ReceiptAndPayment(models.TransientModel):
    _name = 'mgs_payment_integration.receipt_and_payment'
    _description = 'Receipt and Payment'

    journal_id = fields.Many2one('account.journal', string="Journal", domain=[
                                 ('type', 'in', ['bank', 'cash'])])
    partner_id = fields.Many2one('res.partner', string="Customer/Meter#")
    user_id = fields.Many2one('res.users', string='User')
    date_from = fields.Date(
        'From', default=lambda self: fields.Date.today())
    date_to = fields.Date('To', default=lambda self: fields.Date.today())
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    payment_type = fields.Selection([('Receipt', 'Receipt'), ('Payment', 'Payments')],
                                    string='Payment Type', default='Receipt', required=True)
    mgs_sender_phone = fields.Char('Sender Phone')
    mgs_transaction_ref = fields.Char('Transaction #')
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    
    group_by_option = fields.Selection(string='Group By', selection=[('cashier', 'Cashier'), ('account', 'Account')])
    

    @api.constrains('date_from', 'date_to')
    def _check_the_date_from_and_to(self):
        if self.date_to and self.date_from and self.date_to < self.date_from:
            raise ValidationError('''From Date should be less than To Date.''')



    def confirm(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'partner_id': [self.partner_id.id, self.partner_id.name],
                'journal_id': [self.journal_id.id, self.journal_id.name],
                'user_id': [self.user_id.id, self.user_id.name],
                'date_from': self.date_from,
                'date_to': self.date_to,
                'company_id': [self.company_id.id, self.company_id.name],
                'payment_type': self.payment_type,
                'mgs_sender_phone': self.mgs_sender_phone,
                'mgs_transaction_ref': self.mgs_transaction_ref,
                "group_by_option": self.group_by_option
            },
        }

        return self.env.ref('mgs_payment_integration.action_receipt_and_payment').report_action(self, data=data)

    
    
