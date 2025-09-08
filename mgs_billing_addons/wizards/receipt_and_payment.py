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
            },
        }

        return self.env.ref('mgs_billing_addons.action_receipt_and_payment').report_action(self, data=data)

    def export_to_excel(self):
        receipt_and_payment_report_obj = self.env['report.mgs_billing_addons.receipt_and_payment_report']
        lines = receipt_and_payment_report_obj._lines
        # self, self.date_from, self.date_to, self.company_id.id, self.partner_id.id, self.user_id.id, is_group

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        filename = 'MGSPaymentandReceiptReport'
        worksheet = workbook.add_worksheet(filename)

        heading_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'bold': True, 'size': 14})
        sub_heading_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'bold': True, 'size': 12})
        cell_text_format = workbook.add_format(
            {'align': 'left', 'bold': True, 'size': 12})
        cell_number_format = workbook.add_format(
            {'align': 'right', 'bold': True, 'size': 12})
        align_right = workbook.add_format({'align': 'right'})
        align_right_total = workbook.add_format(
            {'align': 'right', 'bold': True})
        date_heading_format = workbook.add_format(
            {'align': 'left', 'bold': True, 'size': 12, 'num_format': 'd-m-yyyy'})
        date_format = workbook.add_format(
            {'align': 'left', 'num_format': 'd-m-yyyy'})

        # Heading
        row = 1
        worksheet.merge_range(
            'A1:G1', self.company_id.name, sub_heading_format)
        row += 1
        worksheet.merge_range(
            'A2:G3', 'Payment Report', heading_format)

        # Search criteria
        row += 2
        column = -1
        if self.date_from:
            row += 1
            worksheet.write(row, column+1, 'From Date', cell_text_format)
            worksheet.write(row, column+2, self.date_from or '',
                            date_heading_format)

        if self.date_to:
            row += 1
            column = -1
            worksheet.write(row, column+1, 'To Date', cell_text_format)
            worksheet.write(row, column+2, self.date_to or '',
                            date_heading_format)

        if self.partner_id:
            row += 1
            column = -1
            worksheet.write(row, column+1, 'Partner', cell_text_format)
            worksheet.write(row, column+2, self.partner_id.name or '')

        if self.journal_id:
            row += 1
            column = -1
            worksheet.write(row, column+1, 'Journal', cell_text_format)
            worksheet.write(row, column+2, self.journal_id.name or '')

        if self.user_id:
            row += 1
            column = -1
            worksheet.write(row, column+1, 'User', cell_text_format)
            worksheet.write(row, column+2, self.user_id.name or '')

        if self.payment_type:
            row += 1
            column = -1
            worksheet.write(row, column+1, 'Payment Type', cell_text_format)
            worksheet.write(row, column+2, self.payment_type or '')

        if self.mgs_sender_phone:
            row += 1
            column = -1
            worksheet.write(row, column+1, 'Sender', cell_text_format)
            worksheet.write(row, column+2, self.mgs_sender_phone or '')

        if self.mgs_transaction_ref:
            row += 1
            column = -1
            worksheet.write(row, column+1, 'Transaction #', cell_text_format)
            worksheet.write(row, column+2, self.mgs_transaction_ref or '')

        # Sub headers
        row += 2
        column = -1
        worksheet.write(row, column+1, 'Date', cell_text_format)
        worksheet.write(row, column+2, 'Number', cell_text_format)
        worksheet.write(row, column+3, 'Partner', cell_text_format)
        worksheet.write(row, column+4, 'Journal', cell_text_format)
        worksheet.write(row, column+5, 'Sender #', cell_text_format)
        worksheet.write(row, column+6, 'Transaction #', cell_text_format)
        worksheet.write(row, column+7, 'Total', cell_number_format)

        total_amount = 0

        for line in lines(self.date_from, self.date_to, self.company_id.id, self.partner_id.id, self.journal_id.id, self.user_id.id, self.payment_type, self.mgs_sender_phone, self.mgs_transaction_ref):
            row += 2
            column = -1
            worksheet.write(row, column+1, line['date'], date_format)
            worksheet.write(row, column+2, line['receipt_no'])
            worksheet.write(row, column+3, line['partner_name'])
            worksheet.write(row, column+4, line['journal_name'])
            worksheet.write(row, column+5, line['mgs_sender_phone'])
            worksheet.write(row, column+6, line['mgs_transaction_ref'])
            worksheet.write(
                row, column+7, '{:,.2f}'.format(line['amount_paid']), align_right)

            total_amount += line['amount_paid']

        row += 2
        column = -1
        worksheet.write(row, column+1, 'Total', cell_text_format)
        worksheet.write(
            row, column+7, '{:,.2f}'.format(total_amount), cell_number_format)

        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        self.write({'datas': out, 'datas_fname': filename})
        fp.close()
        filename += '%2Exlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model='+self._name+'&id='+str(self.id)+'&field=datas&download=true&filename='+filename,
        }


class ReceiptAndPaymentReport(models.AbstractModel):
    _name = 'report.mgs_billing_addons.receipt_and_payment_report'
    _description = 'Receipt and Payment Report'

    @api.model
    def _lines(self, date_from, date_to, company_id, partner_id, journal_id, user_id, payment_type, mgs_sender_phone, mgs_transaction_ref):
        # p_type = 'outbound' if payment_type == 'Receipt' else 'inbound'

        p_type = 'asset_receivable' if payment_type == 'Receipt' else 'liability_payable'

        params = [p_type]

        query = """
        select am.name as receipt_no, rp.id as partner_id, rp.name as partner_name, aml.name as ref,
        rp.mobile as phone, aml.date as date, sum(aml.credit-aml.debit) as amount_paid, aj.name as journal_name,
        ap.mgs_transaction_ref as mgs_transaction_ref, mgs_sender_phone as mgs_sender_phone
        from account_move_line as aml
        left join res_partner as rp on aml.partner_id=rp.id
        left join account_journal as aj on aml.journal_id=aj.id
        left join account_move as am on aml.move_id=am.id
        left join account_payment as ap on am.payment_id=ap.id
        left join account_account as aa on aml.account_id=aa.id
        where aml.parent_state = 'posted' and aa.account_type = %s
        and aj.type in ('bank', 'cash')"""

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
            query += """ and aml.partner_id = """ + str(partner_id)

        if journal_id:
            query += """ and aml.journal_id = """ + str(journal_id)

        if user_id:
            query += """ and aml.create_uid = """ + str(user_id)

        if company_id:
            query += """ and aml.company_id = """ + str(company_id)

        if mgs_sender_phone:
            query += """ and ap.mgs_sender_phone ilike '%s'""" % mgs_sender_phone

        if mgs_transaction_ref:
            query += """ and ap.mgs_transaction_ref ilike '%s'""" % mgs_transaction_ref

        query += """
        group by am.name, rp.id, rp.name, aml.name, rp.mobile, aml.date, aj.name, ap.mgs_transaction_ref, ap.mgs_sender_phone
        order by aml.date"""

        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        return res

        # domain = [('is_internal_transfer', '=', True)]

        # domain.append(('payment_type', '=', 'outbound')) if payment_type == 'Receipt' else domain.append(
        #     ('payment_type', '=', 'intbound'))

        # domain.append(('state', '=', 'posted'))

        # if date_from:
        #     domain.append(('date', '>=', date_from))

        # if date_to:
        #     domain.append(('date', '<=', date_to))

        # if partner_id:
        #     domain.append(('partner_id', '=', partner_id))

        # if journal_id:
        #     domain.append(('journal_id', '=', journal_id))

        # if user_id:
        #     domain.append(('create_uid', '=', user_id))

        # if company_id:
        #     domain.append(('company_id', '=', company_id))

        # res = self.env['account.payment'].search(domain)
        # return res

    @ api.model
    # def _get_report_values(self, docids, data=None):
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
