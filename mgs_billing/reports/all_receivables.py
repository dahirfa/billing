
from odoo import models, fields, api, tools, _
from odoo.http import request
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils
from odoo.addons.portal.controllers.portal import pager as portal_pager
from collections import OrderedDict
import logging
_logger = logging.getLogger(__name__)


class MgsSaleReport(models.Model):
    _name = 'mgs_billing.receivables.report'
    _description = 'mgs_billing.receivables.report'
    _auto = False
    _order = "id DESC"

    def Get_dashboard(self, date_from, date_to, collector):
        where_clause = " AND collector.id = %s" % collector

        select = """SELECT COUNT(DISTINCT rp.id) as count, 
        COALESCE(sum (aml.debit-aml.credit), 0.0) balance"""
        query = "%s %s %s" % (select, self._from(), self._where(
            date_from, date_to, "('posted')", where_clause))

        self.env.cr.execute(query)
        result = self.env.cr.dictfetchone()
        return {
            "result": [result['count'], result['balance']]
        }

    def view_portal_receivables_report(self, values, zone=None, collector=None, date=fields.Date.today(), page=1, sortby=None, filterby='current_month_gt4', search=None, groupby='none', search_in='property_name', **kw):

        # partner = collector
        partner = collector if collector else None
        collector = collector if collector else None
        zone = zone if zone else None
        today = date
        user_id = self.env.user.id

        self.env['mgs_billing.receivables.wizard'].drop_records(user_id)

        next_month = today - relativedelta(months=1)

        start = request.env.company.billing_period_start
        end = request.env.company.billing_period_end

        dates = date_utils.get_billing_start_and_end_dates(today, start, end)

        # date_from = dates[0]
        # date_to = dates[1]

        old_month_dates = date_utils.get_billing_start_and_end_dates(
            next_month, start, end)

        # select = self._select(self, date_from, date_to)
        # from_query = self._from()
        # where = self._where(self, date_from, date_to,
        #                     "('posted')", where_clause=" ")
        # group = self._group_by()

        searchbar_sortings = {
            'property_name': {'label': _('Meter#'), 'order': "ORDER BY NULLIF(regexp_replace(mbp.name, '\D','','g'), '')::numeric"},
            'display_name': {'label': _('Partner'), 'order': 'ORDER BY display_name asc, id asc'},
            'partner_mobile': {'label': _('Mobile'), 'order': 'ORDER BY partner_mobile asc, id asc'},
            'zone_name': {'label': _('Zone'), 'order': 'ORDER BY zone_name asc, id desc'},
            'initial_balance': {'label': _('Initial Balance'), 'order': 'ORDER BY initial_balance desc, id desc'},
            'invoiced': {'label': _('Invoiced'), 'order': 'ORDER BY invoiced desc, id desc'},
            'paid': {'label': _('Paid'), 'order': 'ORDER BY paid desc, id desc'},
            'balance': {'label': _('Balance'), 'order': 'ORDER BY balance desc, id desc'}
        }

        where_clause = " AND collector.id = %s" % collector

        if search and search_in:
            if search_in == 'property_name':
                where_clause += " AND mbp.name =  '%s'" % search
            if search_in == 'display_name':
                where_clause += " AND rp.complete_name  ILIKE '%s'" % search
            if search_in == 'zone_name':
                where_clause += " AND mbz.name = '%s'" % search

        searchbar_filters = {
            'current_month_gt4': {'label': _('Current Month > 4'), 'domain': '%s %s %s %s' % (self._select(dates[0], dates[1]), self._from(), self._where(dates[0], fields.Date.today(), "('posted')", where_clause), self._group_by() + " HAVING COALESCE(sum (aml.debit-aml.credit), 0.0) > 4")},
            'current_month': {'label': _('Current Month'), 'domain': '%s %s %s %s' % (self._select(dates[0], dates[1]), self._from(), self._where(dates[0], fields.Date.today(), "('posted')", where_clause), self._group_by())},
            'last_month': {'label': _('Previous month'), 'domain': '%s %s %s %s' % (self._select(old_month_dates[0], old_month_dates[1]), self._from(), self._where(old_month_dates[0], old_month_dates[1], "('posted')", where_clause), self._group_by())},
            'last_month_gt4': {'label': _('Previous Month > 4'), 'domain': '%s %s %s %s' % (self._select(old_month_dates[0], old_month_dates[1]), self._from(), self._where(old_month_dates[0], old_month_dates[1], "('posted')", where_clause), self._group_by() + " HAVING COALESCE(sum (aml.debit-aml.credit), 0.0) > 4")},

        }

        searchbar_inputs = {
            'property_name': {'input': 'property_name', 'label': _('Search in Meter #')},
            'display_name': {'input': 'display_name', 'label': _('Search in Partner')},
            'zone_name': {'input': 'zone_name', 'label': _('Search in Zone')},
            # 'more_than': {'input': 'more_than', 'label': _('Search More than')},
            # 'less_than': {'input': 'less_than', 'label': _('Search Less than')},
        }

        # default filter by value
        receivables_count = 0

        if not filterby:
            filterby = 'current_month_gt4'
            receivables_count = self.Get_dashboard(
                dates[0], dates[1], collector)
        elif filterby == 'current_month':
            receivables_count = self.Get_dashboard(
                dates[0], dates[1], collector)
        elif filterby == 'current_month_gt4':
            receivables_count = self.Get_dashboard(
                dates[0], dates[1], collector)
        elif filterby == 'last_month':
            receivables_count = self.Get_dashboard(
                old_month_dates[0], old_month_dates[1], collector)
        elif filterby == 'last_month_gt4':
            receivables_count = self.Get_dashboard(
                old_month_dates[0], old_month_dates[1], collector)

        query = searchbar_filters[filterby]['domain']

        if not sortby:
            sortby = 'property_name'
        query += ' %s' % searchbar_sortings[sortby]['order']
        items_per_page = 80
        url = "/report/receivables"

        pager = portal_pager(
            url=url,
            url_args={'sortby': sortby, 'filterby': filterby},
            total=receivables_count['result'][0],
            page=page,
            step=items_per_page
        )

        query += " LIMIT %s OFFSET %s" % (items_per_page,
                                          pager['offset'])
        request.env.cr.execute(query)
        result = request.env.cr.dictfetchall()

        values.update({
            'page_name': 'All Receivables',
            'pager': pager,
            'default_url': url,

            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,

            'searchbar_inputs': searchbar_inputs,
            'search': search,
            'search_in': search_in,

            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'data': result,
            'total_balance': receivables_count['result'][1],
        })
        return values

    billing_account_id = fields.Many2one(
        'res.partner', string='Billing Account', domain=[('is_tenancy', '=', True)])
    tenant_id = fields.Many2one(
        'mgs_billing.partner', related='billing_account_id.customer_id', search='_search_tenant_id')
    mobile = fields.Char(related='tenant_id.mobile',
                         search='_search_tenant_mobile')
    guarantor_id = fields.Many2one('mgs_billing.guarantor', string='Guarantor',
                                   related='tenant_id.guarantor_id', search='_search_guarantor_id')
    guarantor_mobile = fields.Char(
        string='G Mobile', related='guarantor_id.mobile', search='_search_guarantor_mobile')
    property_id = fields.Many2one('mgs_billing.property', string='Property',
                                  related='billing_account_id.property_id', search='_search_property_id')
    zone_id = fields.Many2one('mgs_billing.zone', string='Zone',
                              related='property_id.zone_id', search='_search_zone_id')
    # collector_id = fields.Many2one('res.partner', string='Collector', domain=[(
    #     'is_collector', '=', True)], related='zone_id.collector_id', search='_search_collector_id')
    collector_ids = fields.Many2many('res.partner', string='Collectors', related='zone_id.collector_ids', domain=[('is_collector', '=', True)], tracking=True)
    currency_id = fields.Many2one(
        'res.currency', 'Currency', related='billing_account_id.currency_id')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)
    initial_balance = fields.Monetary()
    invoiced = fields.Monetary()
    paid = fields.Monetary()
    balance = fields.Monetary()

    def _search_tenant_id(self, operator, value):
        return [('billing_account_id.customer_id', '!=', False), ('billing_account_id.customer_id.name', 'ilike', value)]

    def _search_tenant_mobile(self, operator, value):
        return [('billing_account_id.customer_id', '!=', False), ('billing_account_id.customer_id.mobile', 'ilike', value)]

    def _search_guarantor_id(self, operator, value):
        return [('billing_account_id.customer_id', '!=', False), ('billing_account_id.customer_id.guarantor_id', '!=', False), ('billing_account_id.customer_id.guarantor_id.name', 'ilike', value)]

    def _search_guarantor_mobile(self, operator, value):
        return [('billing_account_id.customer_id', '!=', False), ('billing_account_id.customer_id.guarantor_id', '!=', False), ('billing_account_id.customer_id.guarantor_id.mobile', 'ilike', value)]

    def _search_zone_id(self, operator, value):
        return [('billing_account_id.property_id', '!=', False), ('billing_account_id.zone_id', '!=', False), ('billing_account_id.property_id.zone_id.name', 'ilike', value)]

    # TODO: Fix this Collector Search function
    # def _search_collector_id(self, operator, value):
    #     return [('billing_account_id.property_id', '!=', False), ('billing_account_id.zone_id.collector_ids', '!=', False), ('billing_account_id.property_id.zone_id.collector_id.name', 'ilike', value)]

    def _search_property_id(self, operator, value):
        return [('billing_account_id.property_id', '!=', False), ('billing_account_id.property_id.name', 'ilike', value)]

    @api.model
    def _select(self, date_from=fields.Date.today().replace(day=1), date_to=fields.Date.today()):
        return """
    SELECT
        row_number() over (order by rp.id DESC) as id,
        rp.id AS billing_account_id,
        rp.complete_name AS display_name,
        rp.company_id AS company_id,
        mbz.name AS zone_name,
        -- collector.id AS collector_id,
        '' AS collector_id,
        -- collector.name AS collector_name,
        '' AS collector_name,
        mbp.name as property_name,
        rp.mobile as partner_mobile,
        COALESCE(sum(CASE WHEN aml.date < '%s' THEN aml.debit-aml.credit else 0.0 END), 0) AS initial_balance,
        COALESCE(sum(CASE WHEN aml.date between '%s' and '%s' THEN aml.debit else 0.0 END), 0) invoiced,
        COALESCE(sum(CASE WHEN aml.date between '%s'  and '%s'  THEN aml.credit else 0.0 END), 0) paid,
        COALESCE(sum (aml.debit-aml.credit), 0.0) balance
        
        """ % (date_from, date_from, date_to, date_from, date_to)

        # COALESCE(sum (aml.debit-aml.credit), 0.0) balance

    @api.model
    def _from(self):
        return """
            FROM res_partner rp
            LEFT JOIN mgs_billing_property mbp ON rp.property_id = mbp.id
            LEFT JOIN mgs_billing_zone mbz ON mbp.zone_id = mbz.id
            --LEFT JOIN res_partner collector ON mbz.collector_id=collector.id
            --left join res_users as ru on ru.partner_id=collector.id
            LEFT JOIN account_move_line aml ON aml.partner_id=rp.id
            LEFT JOIN account_account AS aa ON aml.account_id = aa.id
            """

    @api.model
    def _where(self, date_from, date_to, move_states="('posted')", where_clause=" "):
        return """WHERE aa.account_type = 'asset_receivable' and aml.partner_id IS NOT NULL AND aml.date <= '%s'
                    AND aml.parent_state IN %s
                    AND rp.is_tenancy = True and mbp.state = 'connected' %s""" % tuple([date_to, move_states, where_clause])

    @api.model
    def _group_by(self):
        # return " GROUP BY rp.id, rp.company_id, mbz.id, collector.id, mbp.name, rp.mobile"
        return " GROUP BY rp.id, rp.company_id, mbz.id, mbp.name, rp.mobile"

    def query_execute(self, having=" ", date_from=fields.Date.today().replace(day=1), date_to=fields.Date.today(), move_states="('posted')", where_clause=" "):
        result = """
        %s 
        %s
        %s
        %s

        %s
        """ % (self._select(date_from, date_to), self._from(), self._where(date_from, date_to, move_states, where_clause), self._group_by(), having)
        # _logger.warning(
        #     '#################################################')
        # _logger.warning(result)
        return result

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute('''CREATE OR REPLACE VIEW %s AS (%s)''' %
                         (self._table, self.query_execute()))
