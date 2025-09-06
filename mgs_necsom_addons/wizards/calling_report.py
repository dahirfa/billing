from odoo import models, fields, api
from odoo.exceptions import ValidationError
import xlsxwriter
import base64
from io import BytesIO


class CallingReport(models.TransientModel):
    _name = 'mgs_necsom_addons.calling_report_wiz'
    _description = 'Calling Report'

    date_from = fields.Date(
        default=fields.Date.today().replace(day=1), required=True)
    date_to = fields.Date(default=fields.Date.today(), required=True)

    zone_id = fields.Many2one('mgs_billing.zone', required=False)
    collector_id = fields.Many2one(
        'res.partner', string='Collector', domain=[('is_collector', '=', True)])
    states = fields.Selection(
        [('all', 'All'), ('posted', 'Posted')], default="posted", string='Target Moves', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    greater_less = fields.Selection(
        [('Greater', 'Greater than'), ('Less', 'Less than')], default="Greater", string='Show', required=True)
    greater_less_amount = fields.Float(
        string='Amount', default=1, required=True)
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
                'date_from': self.date_from,
                'date_to': self.date_to,
                'zone_id': [self.zone_id.id, self.zone_id.name],
                'collector_id': [self.collector_id.id, self.collector_id.name],
                'states': self.states,
                'company_id': [self.company_id.id, self.company_id.name],
                'greater_less': self.greater_less,
                'greater_less_amount': self.greater_less_amount,
            },
        }

        return self.env.ref('mgs_necsom_addons.action_calling_report').report_action(self, data=data)

    def export_to_excel(self):
        calling_report_report_obj = self.env['report.mgs_necsom_addons.calling_report_report']
        lines = calling_report_report_obj._lines
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


class CallingReportReport(models.AbstractModel):
    _name = 'report.mgs_necsom_addons.calling_report_report'
    _description = 'Calling Report Report'

    @api.model
    def _get_payments(self):
        query = "SELECT mgs_sender_phone, partner_id FROM account_payment WHERE mgs_sender_phone IS NOT NULL;"
        self.env.cr.execute(query)
        res = self.env.cr.dictfetchall()
        return res

    @api.model
    def _get_partner_sender_no(self, payments, partner_id):
        filtered_sender_numbers = [str(d['mgs_sender_phone'])
                                   for d in payments if d['partner_id'] == partner_id][:2]
        sender_numbers_string = '/ '.join(filtered_sender_numbers)
        return sender_numbers_string

    @api.model
    def _lines(self, date_from, date_to, zone_id, collector_id, states, company_id, greater_less, greater_less_amount):
        params = [date_from, date_from, date_to,
                  date_from, date_to, date_to]
        query = """
        SELECT
            row_number() over (order by rp.id DESC) as id,
            rp.id AS billing_account_id,
            SPLIT_PART(rp.display_name, '-', 1) AS display_name,
            rp.name AS partner_name,
            rp.company_id AS company_id,
            mbz.name AS zone_name,
            collector.id AS collector_id,
            collector.name AS collector_name,
            mbp.name as property_name,
            rp.mobile as partner_mobile,
            COALESCE(sum(CASE WHEN aml.date < %s THEN aml.debit-aml.credit else 0.0 END), 0) AS initial_balance,
            COALESCE(sum(CASE WHEN aml.date between %s and %s THEN aml.debit else 0.0 END), 0) invoiced,
            COALESCE(sum(CASE WHEN aml.date between %s  and %s  THEN aml.credit else 0.0 END), 0) paid,
            COALESCE(sum (aml.debit-aml.credit), 0.0) balance
        FROM res_partner rp
            LEFT JOIN mgs_billing_property mbp ON rp.property_id = mbp.id
            LEFT JOIN mgs_billing_zone mbz ON mbp.zone_id = mbz.id
            LEFT JOIN res_partner collector ON mbz.collector_id=collector.id
            left join res_users as ru on ru.partner_id=collector.id
            LEFT JOIN account_move_line aml ON aml.partner_id=rp.id
            LEFT JOIN account_account AS aa ON aml.account_id = aa.id
        WHERE aa.account_type = 'asset_receivable' and aml.partner_id IS NOT NULL AND aml.date <= %s
            AND aml.parent_state = 'posted'
            AND rp.is_tenancy = True and mbp.state = 'connected'
        """

        if zone_id:
            params.append(zone_id)
            query += " AND mbz.id = %s"

        if collector_id:
            params.append(collector_id)
            query += " and collector.id = %s"

        if company_id:
            params.append(company_id)
            query += " and aml.company_id = %s"

        query += """
        GROUP BY rp.id, rp.company_id, mbz.id, collector.id, mbp.name, rp.mobile, rp.name"""
        query += " HAVING COALESCE(sum (aml.debit-aml.credit), 0.0) " + \
            "> " + str(greater_less_amount) if greater_less == 'Greater' else "< " + \
            str(greater_less_amount)

        # query += " HAVING COALESCE(sum (aml.debit-aml.credit), 0.0) " + \
        #     "> %s" if greater_less == 'Greater' else "< %s"

        self.env.cr.execute(query, tuple(params))
        lines = []
        res = self.env.cr.dictfetchall()
        return res
        # payments = self._get_payments()
        # for r in res:
        # r['sender_phone'] = self._get_partner_sender_no(
        #     payments, r['billing_account_id'])
        # if payment:
        #     r['sender_phone'] = '/'.join(
        #         payment.mapped('mgs_sender_phone')) or ''
        # else:
        #     sender = self.env['mgs_necsom_addons.old_sys_sender'].search(
        #         [('name', '=', r['property_name']), ('sender_phone', '!=', False)], limit=2)
        #     r['sender_phone'] = '/'.join(
        #         sender.mapped('sender_phone')) or ''
        #     lines.append(r)
        # return lines

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
            'zone_id': data['form']['zone_id'],
            'collector_id': data['form']['collector_id'],
            'states': data['form']['states'],
            'company_id': self.env['res.company'].search([('id', '=', data['form']['company_id'][0])]),
            'greater_less': data['form']['greater_less'],
            'greater_less_amount': data['form']['greater_less_amount'],
            'lines': self._lines,
            'payments': self._get_payments(),
            'get_partner_sender_no': self._get_partner_sender_no
        }
