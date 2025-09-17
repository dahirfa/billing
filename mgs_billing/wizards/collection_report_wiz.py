from odoo import models, fields, api, tools
from datetime import datetime, date
import calendar
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.addons.mgs_billing.controllers.reports import MgsBillingReports
from odoo.http import request
import logging
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


# class MgsCollectionReportPortal(models):

#     def _init_(self):
#         # Create an instance of CustomerPortal
#         self.mgs_customer_portal = MgsBillingReports()
_logger = logging.getLogger(__name__)


class MgsRecivablesReport2(models.Model):
    _name = 'mgs_billing.collection.wizard.line'
    _description = 'CollectionReport'

    id_no = fields.Integer(string='ID')
    display_name = fields.Char(string='Name')
    billing_account_id = fields.Many2one(
        'res.partner', string='Billing Account')
    property_id = fields.Many2one(
        'mgs_billing.property', string='Property', search='_search_property_id')
    property_name = fields.Char()
    zone_id = fields.Many2one(
        'mgs_billing.zone')
    zone_name = fields.Char()
    company_id = fields.Many2one(
        'res.company', string='Company')
    balance = fields.Float('Balance')
    user_id = fields.Many2one('res.users')

    def _search_property_id(self, operator, value):
        return [('property_id.name', '!=', False), ('property_id', '=', value)]


class MgsRecivablesReport(models.TransientModel):
    _name = 'mgs_billing.collection.wizard'
    _description = 'mgs_billing.collection.wizard'

    # def some_method(self):
    #     self.customer_portal.view_portal_billed_report  # Call the function from CustomerPortal
    # @api.model
    # def _get_year(self):
    #     return date.today().year

    # year = fields.Selection(YEARS, string='Year',
    #                         required=True, default=str(date.today().year))
    # month = fields.Selection(MONTHS, string='Month',
    #                          required=True, default=str(date.today().month))
    date_from = fields.Date(default=date.today().replace(day=1))
    date_to = fields.Date(default=date.today())
    zone_id = fields.Many2one('mgs_billing.zone', required=False)
    # collector_id = fields.Many2one('res.partner', string='Collector', domain=[
    #                                ('is_collector', '=', True)])
    collector_ids = fields.Many2many('res.partner', string='Collectors', domain=[('is_collector', '=', True)], tracking=True)
    report_type = fields.Selection([('Billed', 'Billed'), ('Unbilled', 'Unbilled')],
                                   string='Report Type', required=True, default='Unbilled')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)

    def drop_records(self, user_id):
        query = "DELETE FROM mgs_billing_collection_wizard_line WHERE user_id=%s" % user_id
        self.env.cr.execute(query)

    def action_view_report(self, page=1, limit=50):
        collection_report_obj = self.env['mgs.collection.report']
        # next_month = int(self.month) + 1 if self.month != '12' else 1,

        # start = request.env.company.billing_period_start
        # end = request.env.company.billing_period_end
        # last_day = calendar.monthrange(int(self.year), int(self.month))[1]
        # date = '%s-%s-%s' % (self.year, self.month, last_day)
        # date = datetime.strptime(date, "%Y-%m-%d").date()
        # dates = date_utils.get_billing_start_and_end_dates(
        #     date, start, end)
        # date_from = dates[0]
        # date_to = dates[1]
        date_from = self.date_from
        date_to = self.date_to
        allowed_reg_date = self.date_from.replace(day=self.env.company.allowed_reg_date)
        user_id = self.env.user.id
        select = collection_report_obj._select() + ", %s as user_id" % user_id
        group = collection_report_obj._group_by() + ", user_id"

        self.drop_records(user_id)

        query = """
        %s %s %s %s 
        """ % (select, collection_report_obj._from(date_from, date_to), collection_report_obj._where(self.zone_id.id, self.collector_ids.ids, self.company_id.id, allowed_reg_date), group)

        if self.report_type == 'Billed':
            query = query.replace('mbr.id is null', 'mbr.id is NOT null')

        insert_query = """INSERT INTO mgs_billing_collection_wizard_line 
        (id_no, billing_account_id, display_name, property_id, property_name, zone_id, zone_name, company_id, balance, user_id)
        %s""" % query

        self.env.cr.execute(insert_query)

        return {
            'type': 'ir.actions.act_window',
            'name': '%s Houses' % self.report_type,
            'view_mode': 'list,graph',
            'res_model': 'mgs_billing.collection.wizard.line',
            'domain': [('user_id.id', '=', user_id)],
            'context': "{'create': False}",
        }
