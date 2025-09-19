from odoo import models, fields, api, tools
from datetime import datetime, date
import calendar
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils


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


class MgsRecivablesReport2(models.Model):
    _name = 'mgs_billing.receivables.wizard.line'
    _description = 'All Receivables Report'

    id_no = fields.Integer(string='ID')
    billing_account_id = fields.Many2one(
        'res.partner', string='Billing Account')
    display_name = fields.Char(string='Name')
    company_id = fields.Many2one(
        'res.company', string='Company')
    zone_name = fields.Char()
    # collector_id = fields.Many2one(
    #     'res.partner', string='Collector_id')
    collector_ids = fields.Many2many('res.partner', string='Collectors', domain=[('is_collector', '=', True)], tracking=True)
    collector_name = fields.Char(string='Collector')
    initial_balance = fields.Float('Initial Balance')
    invoiced = fields.Float('Invoiced')
    paid = fields.Float('Paid')
    balance = fields.Float('Balance')
    user_id = fields.Many2one('res.users')
    property_name = fields.Char(string='Meter#')
    partner_mobile = fields.Char(string='Mobile')
    total_balance = fields.Float(
        'Total Balance', compute='_compute_total_balance')

    @api.depends('balance')
    def _compute_total_balance(self):
        self.total_balance = sum(self.mapped('balance'))


class MgsRecivablesReport(models.TransientModel):
    _name = 'mgs_billing.receivables.wizard'
    _description = 'Billing Receivables Wizard'

    date_from = fields.Date(default=date.today().replace(day=1))
    date_to = fields.Date(default=date.today())

    @api.model
    def _get_year(self):
        return date.today().year

    # year = fields.Selection(YEARS, string='Year',
    #                         required=True, default=str(date.today().year))
    # month = fields.Selection(MONTHS, string='Month',
    #                          required=True, default=str(date.today().month))

    zone_id = fields.Many2one('mgs_billing.zone', required=False)
    # collector_id = fields.Many2one(
    #     'res.partner', string='Collector', domain=[('is_collector', '=', True)])
    collector_ids = fields.Many2many('res.partner', string='Collectors', domain=[('is_collector', '=', True)], tracking=True)
    states = fields.Selection(
        [('all', 'All'), ('posted', 'Posted')], default="all", string='Target Moves', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    greater_less = fields.Selection(
        [('Greater', 'Greater than'), ('Less', 'Less than')], default="Greater", string='Show', required=True)
    greater_less_amount = fields.Float(
        string='Amount', default=1, required=True)
    include_disconnected = fields.Boolean(
        string='Include Disconnected', default=False)



    # TODO: Fix this Collector Condition



    def drop_records(self, user_id):
        query = "DELETE FROM mgs_billing_receivables_wizard_line WHERE user_id=%s" % user_id
        self.env.cr.execute(query)

    def insert_query(self):
        return "id_no, billing_account_id, user_id, display_name, company_id, zone_name, collector_id, collector_name, property_name, partner_mobile, initial_balance, invoiced, paid, balance"

    def action_view_report(self):
        # start = self.env.company.billing_period_start
        # end = self.env.company.billing_period_end
        # last_day = calendar.monthrange(int(self.year), int(self.month))[1]
        # date = '%s-%s-%s' % (self.year, self.month, last_day)
        # date = datetime.strptime(date, "%Y-%m-%d").date()
        # dates = date_utils.get_billing_start_and_end_dates(
        #     date, start, end)
        # date_from = dates[0]
        # date_to = dates[1]

        date_from = self.date_from
        date_to = self.date_to
        user_id = self.env.user.id

        self.drop_records(user_id)

        report_obj = self.env['mgs_billing.receivables.report']
        move_states = " ('posted') "if self.states == 'posted' else " ('draft','posted') "
        zone_clause = " AND mbz.id = %s" % self.zone_id.id if self.zone_id else " "
        # collector_clause = " AND mbz.collector_id = %s" % self.collector_id.id if self.collector_id else " "
        company_id_clause = " AND aml.company_id = %s " % self.company_id.id if self.company_id else " "
        greater_less_clause = "> %s" % self.greater_less_amount if self.greater_less == 'Greater' else "< %s" % self.greater_less_amount
        having = "HAVING COALESCE(sum (aml.debit-aml.credit), 0.0) " + greater_less_clause
            
        # query = report_obj.query_execute(having, date_from, date_to, move_states, "".join(
        #     (zone_clause, collector_clause, company_id_clause)))
        query = report_obj.query_execute(having, date_from, date_to, move_states, "".join(
            (zone_clause, company_id_clause)))
        query = query.replace('rp.id AS billing_account_id',
                              'rp.id AS billing_account_id, %s as user_id' % user_id)

        if self.include_disconnected:
            query = query.replace(
                "and mbp.state = 'connected'", "and mbp.state in ('connected', 'disconnected')")

        query = query.replace('GROUP BY', 'GROUP BY ru.id, ')
        insert_query = """INSERT INTO mgs_billing_receivables_wizard_line 
        (%s)
        %s""" % (self.insert_query(), query)

        self.env.cr.execute(insert_query)

        # for l in self.env['mgs_billing.receivables.wizard.line'].search([('user_id.id', '=', user_id)]):
        #     l._compute_sender_phone()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Receivables Report',
            'view_mode': 'list,graph',
            'res_model': 'mgs_billing.receivables.wizard.line',
            'domain': [('user_id.id', '=', user_id)],
            'context': "{'create': False}",
        }

        # data = {
        #     'form': {
        #         'date_from': self.date_from,
        #         'date_to': self.date_to,
        #         'zone_id': [self.zone_id.id, self.zone_id.name],
        #         'collector_id': [self.collector_id.id, self.collector_id.name],
        #         'company_id': [self.company_id.id, self.company_id.name],
        #     },
        #     'lines': lines,
        # }
        # return self.env.ref('mgs_billing.action_bill_receivables_report_view').with_context(landscape=False).report_action(self, data=data)
        # print(query)
        # raise ValidationError(query)
        # tools.drop_view_if_exists(self._cr, report_obj._table)
        # self._cr.execute('''CREATE OR REPLACE VIEW %s AS (%s)''' %
        #                  (report_obj._table, query))
        # action = self.env.ref(
        #     'mgs_billing.mgs_billing_receivables_report_action').sudo().read()[0]
        # action['context'] = {}
        # action['context']['create'] = False
        # return action
