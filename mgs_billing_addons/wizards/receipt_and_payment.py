from odoo import models, fields, api
from odoo.exceptions import ValidationError
import xlsxwriter
import base64
from io import BytesIO


class ReceiptAndPayment(models.TransientModel):
    _name = 'mgs_billing_addons.receipt_and_payment'
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

        return self.env.ref('mgs_billing_addons.action_receipt_and_payment').report_action(self, data=data)

    
    

class ReceiptAndPaymentReport(models.AbstractModel):
    _name = 'report.mgs_billing_addons.receipt_and_payment_report'
    _description = 'Receipt and Payment Report'

    @api.model
    def _lines(self, date_from, date_to, company_id, partner_id, journal_id, user_id, payment_type, mgs_sender_phone, mgs_transaction_ref, group_by_option):
        p_type = 'asset_receivable' if payment_type == 'Receipt' else 'liability_payable'
        params = [p_type]

        query = """
        select am.name as receipt_no, rp.id as partner_id, rp.name as partner_name, aml.name as ref,
        rp.mobile as phone, aml.date as date, sum(aml.credit-aml.debit) as amount_paid, aj.name ->> 'en_US'  as journal_name, ap.memo as memo,
        ap.mgs_transaction_ref as mgs_transaction_ref, ap.mgs_sender_phone as mgs_sender_phone, aml.create_uid, ru.id as cashier_id, rup.name as cashier_name    
        from account_move_line as aml
        left join res_partner as rp on aml.partner_id=rp.id
        left join account_journal as aj on aml.journal_id=aj.id
        left join account_move as am on aml.move_id=am.id
        left join account_payment as ap on am.origin_payment_id=ap.id
        left join account_account as aa on aml.account_id=aa.id
        left join res_users ru on aml.create_uid = ru.id
        JOIN res_partner rup ON ru.partner_id = rup.id
        where aml.parent_state = 'posted' and aa.account_type = %s
        and aj.type in ('bank', 'cash')
        """

        if p_type == 'asset_receivable':
            query += """ and aml.credit > 0 """
        else:
            query += """ and aml.debit > 0 """

        if date_from:
            params.append(date_from)
            query += """ and aml.date >= %s"""
        if date_to:
            params.append(date_to)
            query += """ and aml.date <= %s"""
        if partner_id:
            query += """ and aml.partner_id = %s""" % partner_id
        if journal_id:
            query += """ and aml.journal_id = %s""" % journal_id
        if user_id:
            query += """ and aml.create_uid = %s""" % user_id
        if company_id:
            query += """ and aml.company_id = %s""" % company_id
        if mgs_sender_phone:
            query += """ and ap.mgs_sender_phone ilike '%s'""" % mgs_sender_phone
        if mgs_transaction_ref:
            query += """ and ap.mgs_transaction_ref ilike '%s'""" % mgs_transaction_ref

        query += """
        group by am.name, rp.id, rp.name, aml.name, rp.mobile, aml.date, aj.name,
        ap.mgs_transaction_ref, ap.memo, ap.mgs_sender_phone, aml.create_uid, ru.id, rup.name
        order by aml.date
        """

        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()

        # Handle grouping
        if group_by_option == 'cashier':
            grouped = {}
            for r in res:
                cashier = r['cashier_name'] or 'Unknown'
                grouped.setdefault(cashier, []).append(r)
            return grouped
        elif group_by_option == 'account':
            grouped = {}
            for r in res:
                journal = r['journal_name'] or 'Unknown'
                grouped.setdefault(journal, []).append(r)
            return grouped
        else:
            return res



    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'date_from': data['form']['date_from'],
            'date_to': data['form']['date_to'],
            'partner_id': data['form']['partner_id'],
            'journal_id': data['form']['journal_id'],
            'user_id': data['form']['user_id'],
            'company_id': self.env['res.company'].search([('id', '=', data['form']['company_id'][0])]),
            'payment_type': data['form']['payment_type'],
            'mgs_sender_phone': data['form']['mgs_sender_phone'],
            'mgs_transaction_ref': data['form']['mgs_transaction_ref'],
            'lines': self._lines,
        }




