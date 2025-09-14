# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import wizards




    # def export_to_excel(self):
    #     receipt_and_payment_report_obj = self.env['report.mgs_billing_addons.receipt_and_payment_report']
    #     lines = receipt_and_payment_report_obj._lines
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

