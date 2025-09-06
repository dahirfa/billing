# -*- coding: utf-8 -*-
# from odoo import http
from collections import OrderedDict
from dateutil.relativedelta import relativedelta

from odoo import http, fields
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools import date_utils
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import OR, AND
from datetime import date
import logging
# from odoo.addons.mgs_billing.controllers.controllers import PropertyInfoApi
_logger = logging.getLogger(__name__)


class MgsBillingReports(CustomerPortal):
    def get_allowed_zones(self, partner_id):
        return request.env['mgs_billing.zone'].sudo().search([('collector_id', '=', partner_id)])

    def get_user_partner_id(self, user):
        user_id = request.env['res.users'].search([('id', '=', user)])
        return user_id.partner_id.id if user_id else None

    def _query_collection(self, collector_id):
        billing_period_start = request.env.company.billing_period_start
        # billing_period_end  = request.env.company.billing_period_end
        report_obj = request.env['mgs.collection.report']
        # current_date = date.today()
        # last_month = current_date + \
        #     relativedelta(months=-1, day=billing_period_start)
        month = date.today().month
        next_month = month + 1 if month != 12 else 1
        start = request.env.company.billing_period_start
        end = request.env.company.billing_period_end
        dates = date_utils.get_billing_start_and_end_dates(
            date.today(), start, end)
        date_from = dates[0]
        date_to = dates[1]
        # date_from = date.today().replace(day=request.env.company.billing_period_start)
        # date_to = date.today().replace(
        #     month=next_month, day=request.env.company.billing_period_end)
        allowed_reg_date = date.today().replace(
            day=request.env.company.allowed_reg_date)
        _from = report_obj._from(date_from, date_to)
        _where = report_obj._where(None, collector_id, None, allowed_reg_date)
        return _from+_where

    def Get_dashboard(self):
        user = self.get_user_partner_id(request.session.uid)
        from_where = self._query_collection(user)
        select = """SELECT COUNT(DISTINCT mbp.id) as count, 
        COALESCE(sum(CASE WHEN aa.account_type = 'asset_receivable' THEN aml.debit-aml.credit else 0.0 END), 0)AS balance"""
        query = select+from_where

        request.env.cr.execute(query)
        unbilled = request.env.cr.dictfetchone()

        request.env.cr.execute(query.replace(
            'mbr.id is null', 'mbr.id is NOT null'))
        billed = request.env.cr.dictfetchone()
        return {
            "billed": [billed['count'], billed['balance']],
            "unbilled": [unbilled['count'], unbilled['balance']]
        }

    def _prepare_home_portal_values(self, counters):
        """ Add propertie details to main account page """
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        zones = self.get_allowed_zones(partner.id)
        today = fields.Date.today()
        # for receivable
        start = request.env.company.billing_period_start
        end = request.env.company.billing_period_end

        dates = date_utils.get_billing_start_and_end_dates(today, start, end)

        dashboard = self.Get_dashboard()
        receivables_dashboard = request.env['mgs_billing.receivables.report'].Get_dashboard(
            dates[0], dates[1], partner.id)

        if 'billed_count' in counters:
            if partner.is_collector:
                values['billed_count'] = dashboard['billed'][0]
            else:
                values['billed_count'] = 0

        if 'unbilled_count' in counters:
            if partner.is_collector:
                values['unbilled_count'] = dashboard['unbilled'][0]
            else:
                values['unbilled_count'] = 0

        if 'receivables_count' in counters:
            if partner.is_collector:
                values['receivables_count'] = receivables_dashboard['result'][0]
            else:
                values['receivables_count'] = 0

        if 'all_customers_count' in counters:
            # if partner.is_collector:
            #     values['receivables_count'] = receivables_dashboard['result'][0]
            # else:
            values['all_customers_count'] = len(
                request.env['res.partner'].sudo().search([('is_tenancy', '=', True)]).ids)

        return values
    # @http.route(['/report/billed', '/report/billed/page/<int:page>'], type='http', auth="user", website=True)

    @http.route(['/report/billed', '/report/billed/page/<int:page>'], type='http', auth="user", website=True)
    def view_portal_billed_report(self, page=1, sortby=None, filterby='current_month', search=None, groupby='none', search_in='property_name', **kw):
        partner = request.env.user.partner_id.id
        if request.env.user.has_group('mgs_billing.group_billing_user') or request.env.user.has_group('mgs_billing.group_billing_manager'):
            partner = None

        # date = fields.Date.today()
        values = self._prepare_portal_layout_values()
        collection_report_obj = request.env['mgs.collection.report']

        values = collection_report_obj.view_portal_collection_report(
            values, 'billed', None, partner, None, page, sortby, filterby, search, groupby, search_in, **kw)
        return request.render("mgs_billing.bill_collection_report_template", values)

    @http.route(['/report/unbilled', '/report/unbilled/page/<int:page>'], type='http', auth="user", website=True)
    def view_portal_unbilled_report(self, page=1, sortby=None, filterby='current_month', search=None, groupby='none', search_in='property_name', **kw):
        partner = request.env.user.partner_id.id
        if request.env.user.has_group('mgs_billing.group_billing_user') or request.env.user.has_group('mgs_billing.group_billing_manager'):
            partner = None

        values = self._prepare_portal_layout_values()
        collection_report_obj = request.env['mgs.collection.report']
        date = fields.Date.today()

        values = collection_report_obj.view_portal_collection_report(
            values, 'unbilled', None, partner, date, page, sortby, filterby, search, groupby, search_in, **kw)

        return request.render("mgs_billing.bill_collection_report_template", values)

    @http.route(['/report/receivables', '/report/receivables/page/<int:page>'], type='http', auth="user", website=True)
    def view_portal_receivables_report(self, page=1, sortby=None, filterby='current_month_gt4', search=None, groupby='none', search_in='property_name', **kw):
        partner = request.env.user.partner_id.id

        values = self._prepare_portal_layout_values()
        receivables_report_obj = request.env['mgs_billing.receivables.report']
        date = fields.Date.today()

        values = receivables_report_obj.view_portal_receivables_report(
            values, None, partner, date, page, sortby, filterby, search, groupby, search_in, **kw)

        return request.render("mgs_billing.bill_receivables_report_template", values)

    @http.route(['/report/all_customers', '/report/all_customers/page/<int:page>'], type='http', auth="user", website=True)
    def view_portal_all_customers_report(self, page=1, sortby=None, filterby='connected', search=None, groupby='none', search_in='property_name', **kw):
        values = self._prepare_portal_layout_values()
        all_customers_report_obj = request.env['mgs_billing.connect_disconnect.report']
        date = fields.Date.today()

        values = all_customers_report_obj.view_portal_all_customers_report(
            values, 'Connected', None, None, None, page, sortby, filterby, search, groupby, search_in, **kw)

        return request.render("mgs_billing.all_customers_report_template", values)
