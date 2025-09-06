
from odoo import models, fields, api, tools, _
from odoo.http import request
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils
from odoo.addons.portal.controllers.portal import pager as portal_pager
from collections import OrderedDict
import logging
# from odoo.addons.mgs_billing.controllers.controllers import PropertyInfoApi
_logger = logging.getLogger(__name__)


class MgsSaleReport(models.Model):
    _name = 'mgs_billing.connect_disconnect.report'
    _description = 'mgs_billing.connect_disconnect.report'
    _auto = False
    _order = "id DESC"

    def view_portal_all_customers_report(self, values, state='Connected', zone=None, collector=None, company_id=None, page=1, sortby=None, filterby='connected', search=None, groupby='none', search_in='property_name', **kw):
        user_id = self.env.user.id

        searchbar_sortings = {
            'property_name': {'label': _('Meter#'), 'order': "ORDER BY NULLIF(regexp_replace(mbp.name, '\D','','g'), '')::numeric"},
        }

        # where_clause = ""

        # if search and search_in:
        #     if search_in == 'property_name':
        #         where_clause += " AND mbp.name = '%s'" % search
        #     if search_in == 'display_name':
        #         where_clause += " AND rp.complete_name  ILIKE '%s'" % search

        _select = self._select
        _from = self._from
        _where = self._where('connected', zone, collector, company_id)

        if search and search_in:
            if search_in == 'property_name':
                _where += " AND mbp.name = '%s'" % search
            if search_in == 'display_name':
                _where += " AND rp.complete_name  ILIKE '%s'" % search

        searchbar_filters = {
            'connected': {'label': _('Connected Houses'), 'domain': '%s' % (_where)},
            # 'disconnected': {'label': _('Disconnected Houses'), 'domain': '%s %s %s' % (_select(), _from(), _where)},

        }

        searchbar_inputs = {
            'property_name': {'input': 'property_name', 'label': _('Search in Meter #')},
            'display_name': {'input': 'display_name', 'label': _('Search in Partner')},
            # 'more_than': {'input': 'more_than', 'label': _('Search More than')},
            # 'less_than': {'input': 'less_than', 'label': _('Search Less than')},
        }

        self.query_execute('disconnected', None, None, None)

        # query = searchbar_filters[filterby]['domain']

        if not sortby:
            sortby = 'property_name'

        query = '%s %s %s %s' % (_select(), _from(), searchbar_filters[filterby]['domain'],
                                 searchbar_sortings[sortby]['order'])
        items_per_page = 80
        url = "/report/all_customers"

        pager = portal_pager(
            url=url,
            url_args={'sortby': sortby, 'filterby': filterby},
            total=len(
                request.env['res.partner'].sudo().search([('is_tenancy', '=', True)]).ids),
            page=page,
            step=items_per_page
        )

        query += " LIMIT %s OFFSET %s" % (items_per_page,
                                          pager['offset'])


        request.env.cr.execute(query)
        result = request.env.cr.dictfetchall()
        lines = []

        for r in result:
            sub_params = [r['billing_account_id'], 'asset_receivable']
            sub_query = """
                    SELECT sum(debit - credit)
                    FROM account_move_line aml
                    LEFT JOIN account_account as aa ON aml.account_id=aa.id
                    WHERE aml.partner_id = %s
                    AND aa.account_type = %s
                    AND parent_state = 'posted' """
            self.env.cr.execute(sub_query, tuple(sub_params))
            contemp = self.env.cr.fetchone()
            if contemp is not None:
                data = contemp[0] or 0.0
            r['balance'] = data or 0

            lines.append(r)

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
            'data': lines,
        })
        return values

    billing_account_id = fields.Many2one(
        'res.partner', string='Billing Account')
    balance = fields.Monetary('Balance', related='billing_account_id.credit')
    currency_id = fields.Many2one(
        'res.currency', 'Currency', related="billing_account_id.currency_id")
    property_id = fields.Many2one('mgs_billing.property')
    zone_id = fields.Many2one('mgs_billing.zone')
    collector_id = fields.Many2one(
        'res.partner', string='Collector', domain=[('is_collector', '=', True)])
    date = fields.Datetime(string='Date', compute="_compute_date")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)


    def _compute_date(self):
        for rec in self:
            if rec.property_id.state == 'disconnected':
                date = rec.property_id.connection_log_ids.filtered(lambda log: log.state == "disconnected").sorted(key=lambda x: x.time, reverse=False)
                rec.date = date[-1].time if len(date) > 0 else False
            
            elif rec.property_id.state == 'connected':
                date = rec.property_id.connection_log_ids.filtered(lambda log: log.state == "connected").sorted(key=lambda x: x.time, reverse=False)
                rec.date = date[-1].time if len(date) > 0 else rec.property_id.connection_date or False
                
                
            

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

    def _search_collector_id(self, operator, value):
        return [('billing_account_id.property_id', '!=', False), ('billing_account_id.zone_id.collector_id', '!=', False), ('billing_account_id.property_id.zone_id.collector_id.name', 'ilike', value)]

    def _search_property_id(self, operator, value):
        return [('billing_account_id.property_id', '!=', False), ('billing_account_id.property_id.name', 'ilike', value)]

    @api.model
    def _select(self):
        return """
        SELECT mbp.id id, mbp.id property_id, mbp.zone_id zone_id,
        rp.id billing_account_id, rp.company_id company_id, 
        mbz.collector_id collector_id, mbp.name as property_name,
        rp.complete_name as display_name
        """

    @api.model
    def _from(self):
        return """
        FROM mgs_billing_property mbp
        LEFT JOIN mgs_billing_zone mbz ON mbp.zone_id = mbz.id
        LEFT JOIN res_partner rp ON rp.property_id=mbp.id
        """

    @api.model
    def _where(self, state, zone_id, collector_id, company_id):
        result = "WHERE mbp.state = '%s'" % state

        if zone_id:
            result += " AND mbp.zone_id = %s" % zone_id

        if collector_id:
            result += " AND mbz.collector_id = %s" % collector_id

        if company_id:
            result += " AND mbp.company_id = %s" % company_id

        return result

    @api.model
    def _group_by(self):
        return ""

    def query_execute(self, state='disconnected', zone_id=None, collector_id=None, company_id=None):
        result = """
        %s 
        %s
        %s
         
        """ % (self._select(), self._from(), self._where(state, zone_id, collector_id, company_id))
        return result

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute('''CREATE OR REPLACE VIEW %s AS (%s)''' %
                         (self._table, self.query_execute()))
