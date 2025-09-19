from odoo import models, fields, api, tools
from datetime import datetime, date
import xlsxwriter
import base64
from io import BytesIO


def _get_months():
    month_list = []
    for i in range(1, 13):
        month_list.append((str(i), str(i)))
    return month_list


def _get_years():
    year_list = []
    for year in [date.today().year - 1, date.today().year,
                 date.today().year + 1]:
        year_list.append((str(year), str(year)))
    return year_list


MONTHS = _get_months()
YEARS = _get_years()


class MgsRPercentageReport(models.TransientModel):
    _name = 'mgs_billing.percentage.wizard'
    _description = 'Billing Percetage Report Wizard'

    year = fields.Selection(YEARS, string='Year',
                            required=True, default=str(date.today().year))
    month = fields.Selection(MONTHS, string='Month',
                             required=True, default=str(date.today().month))

    zone_id = fields.Many2one('mgs_billing.zone', required=False)
    # collector_id = fields.Many2one(
    #     'res.partner', string='Collector', domain=[('is_collector', '=', True)])
    collector_ids = fields.Many2many('res.partner', string='Collectors', domain=[('is_collector', '=', True)], tracking=True)
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)

    def action_view_report(self):
        year = self.year
        month = int(self.month)
        next_month = month + 1 if month != 12 else 1
        next_year = str(int(year) + 1) if month == 12 else year
        data = {
            'form': {
                'date_from': "%s-%s-%s" % (year, month, self.env.company.billing_period_start),
                'date_to': "%s-%s-%s" % (next_year, str(next_month), self.env.company.billing_period_end),
                'zone_id': [self.zone_id.id, self.zone_id.name],
                # 'collector_id': [self.collector_id.id, self.collector_id.name],
                'collector_ids': self.collector_ids.ids,
                'company_id': [self.company_id.id, self.company_id.name],
            },
        }
        return self.env.ref('mgs_billing.action_percentage_report').report_action(self, data=data)
        # print(query)
        # raise ValidationError(query)
        # tools.drop_view_if_exists(self._cr, report_obj._table)
        # self._cr.execute('''CREATE OR REPLACE VIEW %s AS (%s)''' %
        #                  (report_obj._table, query))

        # action_id = 'mgs_billing.mgs_billing_billed_percentage_report_action' if report_by == 'Billed' else 'mgs_billing.action_bill_percentage_report_view'

        # action = self.env.ref(action_id).sudo().read()[0]
        # action['context'] = {}
        # action['context']['create'] = False
        # return action


    def export_excel(self):
        collection_report_obj = self.env['report.mgs_billing.percentage_report']
        # get_month_name = collection_report_obj._get_month_name
        year = self.year
        month = int(self.month)
        next_month = month + 1 if month != 12 else 1
        next_year = str(int(year) + 1) if month == 12 else year
        date_from = "%s-%s-%s" % (year, month, self.env.company.billing_period_start)
        date_to = "%s-%s-%s" % (next_year, str(next_month), self.env.company.billing_period_end)
        lines = collection_report_obj._lines(date_from, date_to, self.collector_ids.ids,  self.zone_id.id, self.env.company.id)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        filename = '% Of HHS Billed'
        worksheet = workbook.add_worksheet(filename)

        # Formats
        heading_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'bold': True, 'size': 14})
        cell_text_format = workbook.add_format(
            {'align': 'left', 'bold': True, 'size': 12})
        cell_number_format = workbook.add_format(
            {'align': 'right', 'bold': True, 'size': 12})
        align_right_bold = workbook.add_format(
            {'align': 'right', 'bold': True})
        align_right = workbook.add_format({'align': 'right'})
        align_center = workbook.add_format({'align': 'center'})
        align_right_total = workbook.add_format(
            {'align': 'right', 'bold': True})

        # Heading
        row = 1
        worksheet.merge_range('A1:F2', '% Of HHS Billed', heading_format)

        # Search criteria
        row += 1
        column = -1

        # Sub headers
        row += 2
        column = -1
        worksheet.write(row, column+1, 'S/N', cell_text_format)
        worksheet.write(row, column+2, 'Zone', cell_text_format)
        worksheet.write(row, column+3, 'Collector', cell_text_format)
        worksheet.write(row, column+4, 'No of HHS In a Zone', cell_text_format)
        worksheet.write(row, column+5, 'HHS Billed So Far', cell_text_format)
        worksheet.write(row, column+6, '% Of HHS Billed', cell_text_format)
        # worksheet.write(row, column+7, 'Rest', cell_number_format)

        # data
        row += 1
        column = -1

        no = 0
        total_initial_balance = 0
        total_invoiced = 0
        total_balance = 0
        for line in lines:
            row += 1
            column = -1
            no += 1
            worksheet.write(row, column+1, no)
            worksheet.write(row, column+2, line['zone_name'])
            worksheet.write(row, column+3, line['collector_name'])
            worksheet.write(row, column+4, line['property_count'])
            worksheet.write(row, column+5, line['billed_count'])
            worksheet.write(row, column+6, line['percentage'], align_center)
            # worksheet.write(
            #     row, column+7, "{:,}".format(line['initial_balance']), align_right)
            total_initial_balance += line['property_count']
            total_invoiced += line['billed_count']
            # total_balance += line['percentage']

        row += 1
        column = -1
        worksheet.write(row, column+1, '', align_center)
        worksheet.write(row, column+2, '')
        worksheet.write(row, column+3, '')
        worksheet.write(row, column+4, "{:,.2f}".format(total_initial_balance), align_right_bold) 
        worksheet.write(row, column+5, "{:,.2f}".format(total_invoiced), align_right_bold)
        # worksheet.write(row, column+6, "{:,.2f}".format(total_balance), align_right_bold)
        worksheet.write(row, column+6, '')
        # worksheet.write(
        #     row, column+7, "{:,}".format(total_rest), align_right_bold)

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


