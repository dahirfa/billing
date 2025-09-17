
from odoo import models, fields, api, tools, _
from odoo.http import request
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils
from odoo.addons.portal.controllers.portal import pager as portal_pager
from collections import OrderedDict
import logging
_logger = logging.getLogger(__name__)


class CollectionReport(models.Model):
    _name = 'mgs.collection.report'
    _description = 'Collection Report'
    _auto = False

    def Get_dashboard(self, from_where, report_type='unbilled'):
        # user = self.get_user_partner_id(request.session.uid)
        # from_where = self._query_collection(user)
        # code
        select = """SELECT COUNT(DISTINCT mbp.id) as count, 
        COALESCE(sum(CASE WHEN aa.account_type = 'asset_receivable' THEN aml.debit-aml.credit else 0.0 END), 0)AS balance"""
        query = select+from_where
        self.env.cr.execute(query)

        if report_type == 'billed':
            billed = self.env.cr.dictfetchone()
            return {
                "billed": [billed['count'], billed['balance']],
            }
        else:
            unbilled = self.env.cr.dictfetchone()
            return {
                "unbilled": [unbilled['count'], unbilled['balance']]
            }

    def view_portal_collection_report(self, values, report_type='unbilled', zone=None, collector=None, date=None, page=1, sortby=None, filterby='current_month', search=None, groupby='none', search_in='property_name', **kw):

        # partner = collector
        partner = collector if collector else None
        collector = collector if collector else None
        zone = zone if zone else None
        today = date if date else fields.Date.today()
        # partners = self.get_allowed_partners(partner.id)
        # query = self._get_property_domain(partners.ids)

        next_month = today - relativedelta(months=1)

        start = request.env.company.billing_period_start
        end = request.env.company.billing_period_end

        dates = date_utils.get_billing_start_and_end_dates(today, start, end)
        old_month_dates = date_utils.get_billing_start_and_end_dates(
            next_month, start, end)

        select = self._select()
        where = self._where(None, partner, request.env.company.id, dates[0].replace(
            day=request.env.company.allowed_reg_date))
        if report_type == 'billed':
            where = where.replace('mbr.id is null', 'mbr.id is NOT null')
        group = self._group_by()

        searchbar_sortings = {
            'property_name': {'label': _('Property'), 'order': 'ORDER BY property_name asc, id desc'},
            'display_name': {'label': _('Partner'), 'order': 'ORDER BY display_name asc, id asc'},
            'zone_name': {'label': _('Zone'), 'order': 'ORDER BY zone_name asc, id desc'},
            'balance': {'label': _('Balance'), 'order': 'ORDER BY balance desc, id desc'}
        }

        searchbar_filters = {
            'current_month': {'label': _('Current Month'), 'domain': self._from(dates[0], dates[1])},
            'last_month': {'label': _('Previous month'), 'domain': self._from(old_month_dates[0], old_month_dates[1])},
        }

        searchbar_inputs = {
            'property_name': {'input': 'property_name', 'label': _('Search in Meter #')},
            'display_name': {'input': 'display_name', 'label': _('Search in Partner')},
            'zone_name': {'input': 'zone_name', 'label': _('Search in Zone')},
            # 'more_than': {'input': 'more_than', 'label': _('Search More than')},
            # 'less_than': {'input': 'less_than', 'label': _('Search Less than')},
        }

        if search and search_in:
            search_domain = ''
            if search_in == 'property_name':
                search_domain = " AND mbp.name =  '%s'" % search
            if search_in == 'display_name':
                search_domain = " AND rp.complete_name  ILIKE '%s'" % search
            if search_in == 'zone_name':
                search_domain = " AND mbz.name = '%s'" % search

            where += search_domain

        if report_type == 'billed':
            where = where.replace('mbr.id is null', 'mbr.id is NOT null')

        # default filter by value
        if not filterby:
            filterby = 'current_month'
        from_query = searchbar_filters[filterby]['domain']

        if not sortby:
            sortby = 'property_name'
        order = searchbar_sortings[sortby]['order']

        billed_count = self.Get_dashboard(from_query+where, report_type)
        items_per_page = 80
        url = "/report/billed" if report_type == 'billed' else "/report/unbilled"
        pager = portal_pager(
            url=url,
            url_args={'sortby': sortby, 'filterby': filterby},
            total=billed_count[report_type][0],
            page=page,
            step=items_per_page
        )
        query = "%s %s %s %s %s " % (select, from_query, where, group, order)
        query += " LIMIT %s OFFSET %s" % (items_per_page,
                                          pager['offset'])

        request.env.cr.execute(query)
        result = request.env.cr.dictfetchall()

        # rent_group = Rent.search(
        #     domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        # currency = request.env.company.currency_id
        # total_amount = sum(rent_group.mapped('amount')) or 0.0
        # invoice_ids = rent_group.mapped('invoice_id').sudo().filtered(
        #     lambda x: x.state == 'posted')
        # amount_total = sum(invoice_ids.sudo().mapped('amount_total'))
        # amount_residual = sum(invoice_ids.sudo().mapped('amount_residual'))

        # paid_amount = amount_total-amount_residual
        # request.session['my_rent_group_history'] = rent_group.ids[:100]
        values.update({
            'page_name': report_type,
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
            'total_balance': billed_count[report_type][1],
        })
        return values

    billing_account_id = fields.Many2one(
        'res.partner', string='Billing Account')
    balance = fields.Monetary('Balance', related='billing_account_id.credit')
    currency_id = fields.Many2one(
        'res.currency', 'Currency', related="billing_account_id.currency_id")
    property_id = fields.Many2one('mgs_billing.property')
    zone_id = fields.Many2one('mgs_billing.zone')
    # reading_id = fields.Many2one('mgs_billing.reading')
    # date = fields.Date()
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)
    # bill_state = fields.Selection(
    #     [('billed', 'Billed'), ('unbilled', 'Unbilled')], default='unbilled')

    # company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id) Fix me

    @api.model
    def _select(self):
        return """SELECT 
            mbp.id AS id, rp.id AS billing_account_id,
            rp.complete_name AS display_name, mbp.id AS property_id,
            mbp.name AS property_name, mbp.zone_id AS zone_id,
            mbz.name AS zone_name, mbp.company_id AS company_id,
            COALESCE(sum(CASE WHEN aa.account_type = 'asset_receivable' THEN aml.debit-aml.credit else 0.0 END), 0) balance           
        """

    @api.model
    def _from(self, date_from=fields.Date.today().replace(day=1), date_to=fields.Date.today()):
        return """
            FROM mgs_billing_property mbp    
            LEFT JOIN mgs_billing_zone mbz ON mbp.zone_id=mbz.id
            LEFT JOIN res_partner rp ON mbp.id=rp.property_id
            LEFT JOIN account_move_line aml ON aml.partner_id=rp.id
            LEFT JOIN account_account aa ON aml.account_id=aa.id
            LEFT JOIN mgs_billing_reading mbr ON mbr.property_id=mbp.id and mbr.date between '%s' AND '%s' and mbr.state = 'posted'
            """ % (date_from, date_to)

        # return """
        #     FROM mgs_billing_reading mbr
        #     RIGHT JOIN mgs_billing_property mbp on mbr.property_id=mbp.id
        #     LEFT JOIN mgs_billing_zone mbz on mbp.zone_id=mbz.id
        #     LEFT JOIN res_partner rp on mbp.id=rp.property_id
        #     """

    @api.model
    def _where(self, zone_id=None, collector_id=None, company_id=None, allowed_reg_date=fields.date.today().replace(day=15)):
        
        if self.env.company.is_allow_reg_date:        
            #! Removed the property state check from the below condition
            #! and mbp.state = 'connected'
            result = "where mbr.id is null and connection_date <= '%s'" % allowed_reg_date
        else:
            #! Removed the property state check from the below condition
            #! and mbp.state = 'connected'
            result = "where mbr.id is null"

        if zone_id:
            result += " AND mbp.zone_id = %s" % zone_id

        # TODO: Fix this Collector Condition
        # if collector_id:
        #     result += " AND mbz.collector_ids in %s" % [collector_id]

        if company_id:
            result += " AND mbp.company_id = %s" % company_id

        return result

    @api.model
    def _group_by(self):
        return """
        GROUP BY mbp.id, rp.id,rp.complete_name,
        mbp.name, mbp.zone_id,
        mbz.name, mbp.company_id
    """

    def query_execute(self, date_from=fields.Date.today().replace(day=1), date_to=fields.Date.today(), zone_id=None, collector_id=None, company_id=None, allowed_reg_date=fields.date.today().replace(day=15)):
        result = """
        %s 
        
        %s

        %s

        %s 
        """ % (self._select(), self._from(date_from, date_to), self._where(zone_id, collector_id, company_id, allowed_reg_date), self._group_by())
        return result

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute('''CREATE OR REPLACE VIEW %s AS (%s)''' %
                         (self._table, self.query_execute()))
