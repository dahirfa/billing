from odoo import models, fields, api, tools
from datetime import datetime, date
import calendar
from odoo.exceptions import UserError, ValidationError


def _get_months():
    year_list = []
    for i in range(1, 13):
        year_list.append((str(i), str(i)))
    return year_list


MONTHS = _get_months()


class MeterCubicSoldReportWiz(models.TransientModel):
    _name = 'mgs_billing.meter_cubic_sold.wizard'
    _description = 'mgs_billing.meter_cubic_sold.wizard'

    @api.model
    def _get_year(self):
        return date.today().year

    year = fields.Char(default=_get_year, string='Year', required=True)
    month = fields.Selection(MONTHS, string='Month',
                             required=True, default=str(date.today().month))
    zone_id = fields.Many2one('mgs_billing.zone', required=False)
    collector_id = fields.Many2one(
        'res.partner', string='Collector', domain=[('is_collector', '=', True)])

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    report_by = fields.Selection(
        [('Zone', 'Zone'), ('Collector', 'Collector')], string='Report by', default='Zone')

    def action_view_report(self):
        monthrange = calendar.monthrange(int(self.year), int(self.month))
        date_from = self.year + '/' + str(self.month) + '/1'
        date_to = self.year + '/' + str(self.month) + '/' + str(monthrange[1])
        report_obj = self.env['mgs_billing.meter_cubic_sold.report']

        query = report_obj.query_execute(self.report_by,
                                         date_from, date_to, self.zone_id.id, self.collector_id.id, self.company_id.id)
        self.env.cr.execute(query)
        lines = self.env.cr.dictfetchall()
        data = {
            'form': {
                'report_by': self.report_by,
                'year': self.year,
                'month': self.month,
                'zone_id': [self.zone_id.id, self.zone_id.name],
                'collector_id': [self.collector_id.id, self.collector_id.name],
                'company_id': [self.company_id.id, self.company_id.name],
            },
            'lines': lines,
        }
        return self.env.ref('mgs_billing.action_bill_meter_cubic_sold_report_view').with_context(landscape=False).report_action(self, data=data)
        # print(query)
        # raise ValidationError(query)
        # tools.drop_view_if_exists(self._cr, report_obj._table)
        # self._cr.execute('''CREATE OR REPLACE VIEW %s AS (%s)''' %
        #                  (report_obj._table, query))
        # action = self.env.ref(
        #     'mgs_billing.mgs_billing_meter_cubic_sold_report_action').sudo().read()[0]
        # if self.report_by == 'collector':
        #     action = self.env.ref(
        #         'mgs_billing.mgs_billing_meter_cubic_sold_report_action2').sudo().read()[0]

        # action['context'] = {}
        # action['context']['create'] = False
        # return action
