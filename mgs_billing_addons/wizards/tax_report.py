from odoo import models, fields, api
from odoo.exceptions import ValidationError
import xlsxwriter
import base64
from io import BytesIO


class TaxReport(models.TransientModel):
    _name = 'mgs_billing_addons.tax_report'
    _description = 'Tax Report'

    account_id = fields.Many2one(
        'account.account', string="Account", required=True)
    date_from = fields.Date(
        'From', default=lambda self: fields.Date.today())
    date_to = fields.Date('To', default=lambda self: fields.Date.today())
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    report_type = fields.Selection([('Not Paid', 'Not Paid'), ('Paid', 'Paid')],
                                   string='Report Type', default='Not Paid', required=True)

    @api.onchange('account_id')
    def onchange_account_id(self):
        # if self.account_id:
        return {'domain': {'account_id': [('id', 'in', self.env.company.mgs_tax_account_ids.ids)]}}

    @api.constrains('date_from', 'date_to')
    def _check_the_date_from_and_to(self):
        if self.date_to and self.date_from and self.date_to < self.date_from:
            raise ValidationError('''From Date should be less than To Date.''')

    def confirm(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'account_id': [self.account_id.id, self.account_id.name],
                'date_from': self.date_from,
                'date_to': self.date_to,
                'company_id': [self.company_id.id, self.company_id.name],
                'report_type': self.report_type
            },
        }

        return self.env.ref('mgs_billing_addons.action_mgs_tax_report').report_action(self, data=data)

    # def export_to_excel(self):
    #     tax_report_report_obj = self.env['report.mgs_billing_addons.tax_report_report']
    #     lines = tax_report_report_obj._lines
    #     # self, self.date_from, self.date_to, self.company_id.id, self.partner_id.id, self.user_id.id, is_group

    #     fp = BytesIO()
    #     workbook = xlsxwriter.Workbook(fp)
    #     filename = 'MGSPaymentandReceiptReport'
    #     worksheet = workbook.add_worksheet(filename)

    #     heading_format = workbook.add_format(
    #         {'align': 'center', 'valign': 'vcenter', 'bold': True, 'size': 14})
    #     sub_heading_format = workbook.add_format(
    #         {'align': 'center', 'valign': 'vcenter', 'bold': True, 'size': 12})
    #     cell_text_format = workbook.add_format(
    #         {'align': 'left', 'bold': True, 'size': 12})
    #     cell_number_format = workbook.add_format(
    #         {'align': 'right', 'bold': True, 'size': 12})
    #     align_right = workbook.add_format({'align': 'right'})
    #     align_right_total = workbook.add_format(
    #         {'align': 'right', 'bold': True})
    #     date_heading_format = workbook.add_format(
    #         {'align': 'left', 'bold': True, 'size': 12, 'num_format': 'd-m-yyyy'})
    #     date_format = workbook.add_format(
    #         {'align': 'left', 'num_format': 'd-m-yyyy'})

    #     # Heading
    #     row = 1
    #     worksheet.merge_range(
    #         'A1:G1', self.company_id.name, sub_heading_format)
    #     row += 1
    #     worksheet.merge_range(
    #         'A2:G3', 'Payment Report', heading_format)

    #     # Search criteria
    #     row += 2
    #     column = -1
    #     if self.date_from:
    #         row += 1
    #         worksheet.write(row, column+1, 'From Date', cell_text_format)
    #         worksheet.write(row, column+2, self.date_from or '',
    #                         date_heading_format)

    #     if self.date_to:
    #         row += 1
    #         column = -1
    #         worksheet.write(row, column+1, 'To Date', cell_text_format)
    #         worksheet.write(row, column+2, self.date_to or '',
    #                         date_heading_format)

    #     if self.partner_id:
    #         row += 1
    #         column = -1
    #         worksheet.write(row, column+1, 'Partner', cell_text_format)
    #         worksheet.write(row, column+2, self.partner_id.name or '')

    #     if self.journal_id:
    #         row += 1
    #         column = -1
    #         worksheet.write(row, column+1, 'Journal', cell_text_format)
    #         worksheet.write(row, column+2, self.journal_id.name or '')

    #     if self.user_id:
    #         row += 1
    #         column = -1
    #         worksheet.write(row, column+1, 'User', cell_text_format)
    #         worksheet.write(row, column+2, self.user_id.name or '')

    #     if self.payment_type:
    #         row += 1
    #         column = -1
    #         worksheet.write(row, column+1, 'Payment Type', cell_text_format)
    #         worksheet.write(row, column+2, self.payment_type or '')

    #     if self.mgs_sender_phone:
    #         row += 1
    #         column = -1
    #         worksheet.write(row, column+1, 'Sender', cell_text_format)
    #         worksheet.write(row, column+2, self.mgs_sender_phone or '')

    #     if self.mgs_transaction_ref:
    #         row += 1
    #         column = -1
    #         worksheet.write(row, column+1, 'Transaction #', cell_text_format)
    #         worksheet.write(row, column+2, self.mgs_transaction_ref or '')

    #     # Sub headers
    #     row += 2
    #     column = -1
    #     worksheet.write(row, column+1, 'Date', cell_text_format)
    #     worksheet.write(row, column+2, 'Number', cell_text_format)
    #     worksheet.write(row, column+3, 'Partner', cell_text_format)
    #     worksheet.write(row, column+4, 'Journal', cell_text_format)
    #     worksheet.write(row, column+5, 'Sender #', cell_text_format)
    #     worksheet.write(row, column+6, 'Transaction #', cell_text_format)
    #     worksheet.write(row, column+7, 'Total', cell_number_format)

    #     total_amount = 0

    #     for line in lines(self.date_from, self.date_to, self.company_id.id, self.partner_id.id, self.journal_id.id, self.user_id.id, self.payment_type, self.mgs_sender_phone, self.mgs_transaction_ref):
    #         row += 2
    #         column = -1
    #         worksheet.write(row, column+1, line['date'], date_format)
    #         worksheet.write(row, column+2, line['receipt_no'])
    #         worksheet.write(row, column+3, line['partner_name'])
    #         worksheet.write(row, column+4, line['journal_name'])
    #         worksheet.write(row, column+5, line['mgs_sender_phone'])
    #         worksheet.write(row, column+6, line['mgs_transaction_ref'])
    #         worksheet.write(
    #             row, column+7, '{:,.2f}'.format(line['amount_paid']), align_right)

    #         total_amount += line['amount_paid']

    #     row += 2
    #     column = -1
    #     worksheet.write(row, column+1, 'Total', cell_text_format)
    #     worksheet.write(
    #         row, column+7, '{:,.2f}'.format(total_amount), cell_number_format)

    #     workbook.close()
    #     out = base64.encodebytes(fp.getvalue())
    #     self.write({'datas': out, 'datas_fname': filename})
    #     fp.close()
    #     filename += '%2Exlsx'

    #     return {
    #         'type': 'ir.actions.act_url',
    #         'target': 'new',
    #         'url': 'web/content/?model='+self._name+'&id='+str(self.id)+'&field=datas&download=true&filename='+filename,
    #     }


class TaxReportReport(models.AbstractModel):
    _name = 'report.mgs_billing_addons.tax_report_report'
    _description = 'Tax Report Report'

    @api.model
    def _lines(self, date_from, date_to, company_id, account_id, report_type):
        # payment_status = ['not_paid', 'partial'] if report_type == 'Not Paid' else [
        #     'paid', 'in_payment']
        domain = [('parent_state', '=', 'posted')]

        if report_type == 'Not Paid':
            domain.append(('move_id.amount_residual', '>', 0))
        else:
            domain.append(('move_id.amount_residual', '=', 0))

        if date_from:
            domain.append(('date', '>=', date_from))

        if date_to:
            domain.append(('date', '<=', date_to))

        if account_id:
            domain.append(('account_id', '=', account_id))

        if company_id:
            domain.append(('company_id', '=', company_id))

        result = self.env['account.move.line'].sudo().search(domain)
        return result

    @api.model
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
            'account_id': data['form']['account_id'],
            'company_id': self.env['res.company'].search([('id', '=', data['form']['company_id'][0])]),
            'report_type': data['form']['report_type'],
            'lines': self._lines,
        }
