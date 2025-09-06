# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.addons.mgs_billing.controllers.controllers import PropertyInfoApi

from odoo.http import request
from datetime import date
from odoo.tools import date_utils

import logging

_logger = logging.getLogger(__name__)


class PropertyInfoApiOverride(PropertyInfoApi):
    def _query_collection(self, collector_id):
        report_obj = request.env['mgs.collection.report']
        start = request.env.company.billing_period_start
        end = request.env.company.billing_period_end
        dates = date_utils.get_billing_start_and_end_dates(
            date.today(), start, end)
        date_from = dates[0]
        date_to = date.today()
        allowed_reg_date = dates[0].replace(
            day=request.env.company.allowed_reg_date)
        _from = report_obj._from(date_from, date_to)
        _where = report_obj._where(None, collector_id, None, allowed_reg_date)
        _where +=""" AND (
            mbp.meter_type != 'smart'
            OR (mbp.meter_type = 'smart' AND mbp.auto_reset = TRUE)) 
        """
        return _from+_where


    @http.route('/billingApi/properties/dashboard/', type='json', auth='user')
    def Get_dashboard(self):
        user = self.get_user_partner_id(request.session.uid)
        from_where = self._query_collection(user)
        select = """SELECT COUNT(DISTINCT mbp.id)"""
        query = select+from_where

        request.env.cr.execute(query)
        unbilled = request.env.cr.fetchone()

        request.env.cr.execute(query.replace(
            'mbr.id is null', 'mbr.id is NOT null'))
        billed = request.env.cr.fetchone()
        return {
            "billed": billed[0],
            "unbilled": unbilled[0]
        }

    @http.route('/billingApi/properties/unbilled/', type='json', auth='user')
    def get_collector_re_properties(self, **kw):
        user = self.get_user_partner_id(request.session.uid)
        from_where = self._query_collection(user)
        meter_no = kw.get("id", False)
        if meter_no:
            from_where += " AND mbp.name='%s' " % meter_no

        select = """SELECT rp.id partner_id, rp.name partner_name, mbp.name property_id, mbp.state state, rp.street address, rp.mobile,
        COALESCE(sum(CASE WHEN aa.account_type = 'asset_receivable' THEN aml.debit-aml.credit else 0.0 END), 0) as balance"""
        query = select + from_where + \
            "group by rp.id, rp.name, mbp.name, mbp.state, rp.street, rp.mobile"

        request.env.cr.execute(query)
        data = request.env.cr.dictfetchall()

        return {'data': data}

    @http.route('/billingApi/properties/billed/', type='json', auth='user')
    def get_collector_properties(self, **kw):
        user = self.get_user_partner_id(request.session.uid)
        from_where = self._query_collection(user)
        from_where = from_where.replace('mbr.id is null', 'mbr.id is NOT null')
        meter_no = kw.get("id", False)
        if meter_no:
            from_where += " AND mbp.name='%s' " % meter_no
        select = """SELECT rp.id partner_id, rp.name partner_name, mbp.name property_id, mbp.state state, rp.street address, rp.mobile,
        COALESCE(sum(CASE WHEN aa.account_type = 'asset_receivable' THEN aml.debit-aml.credit else 0.0 END), 0) as balance"""
        query = select + from_where + \
            "group by rp.id, rp.name, mbp.name, mbp.state, rp.street, rp.mobile"
        request.env.cr.execute(query)
        data = request.env.cr.dictfetchall()
        return {'data': data}

    def get_user_partner_id(self, user):
        user_id = request.env['res.users'].search([('id', '=', user)])
        return user_id.partner_id.id if user_id else None

    @http.route('/billingApi/getPropertyInfo/', type='json', auth='user')
    def getPropertyInfo(self, **kw):
        collector_id = self.get_user_partner_id(request.session.uid)
        month = date.today().month
        _logger.error(request.httprequest.remote_addr)
        start = request.env.company.billing_period_start
        end = request.env.company.billing_period_end
        dates = date_utils.get_billing_start_and_end_dates(date.today(), start, end)
        if date.today() > dates[1]:
            return {
                "response": "Error: Period Time Over"
            }
        allowed_reg_date = dates[0].replace(
            day=int(request.env.company.allowed_reg_date))
        partner_obj = request.env['res.partner']
        domain = [
            ('property_id.name', '=', kw.get("id")),
            ('property_id.connection_date', '<=', allowed_reg_date),
            ('property_id.zone_id.collector_id.id', '=', collector_id),
            ('property_id.state', '=', 'connected'),
            '|', ('property_id.meter_type', '!=', 'smart'),
            '&', ('property_id.meter_type', '=', 'smart'),
            ('property_id.auto_reset', '=', True)]
        
        partner_id = partner_obj.sudo().search(domain, limit=1)
        property_id = partner_id.property_id
        avg = partner_id.average_usage
        mobile = partner_id.mobile if partner_id.mobile else"N/A"

        if not partner_id:
            return {
                "response": "House not found"
            }

        data = {
            "partner_id": partner_id.id,
            "partner_name": partner_id.name,
            "partner_mobile": "".join(mobile.split()),
            "zone_name": property_id.zone_id.name,
            "property_name": property_id.name,
            "property_id": property_id.name,
            "max_above_avg": request.env.company.max_above_avg * avg,
            "max_under_avg": request.env.company.max_under_avg * avg,
            "average_usage": partner_id.average_usage
        }
        if data['partner_id']:
            is_billed = request.env['mgs_billing.reading'].sudo(
            )._get_billed_unbilled(date.today(), property_id.id)
            data.update({
                'perv_bal': self.get_partner_previous_balance(data['partner_id'], " AND aml.date <= '%s'" % date.today()),
                'last_reading': self.get_last_reading(data['property_id']) or 0,
                'invoice_state': 'Billed' if is_billed else 'Not Billed'
            })
            return data

        return {
            "response": "House not found"
        }

    @http.route('/billingApi/createMeterReading/', type='json', auth='user', methods=['POST'], csrf=False)
    def createMeterReading(self, **kw):
        
        request_data = request.httprequest.data
        property_id = kw.get("property_id")
        mobile = kw.get("mobile")
        date = fields.Date().today()
        current_reading = kw.get("current_reading")
        reading_obj = http.request.env['mgs_billing.reading']
        
        start = request.env.company.billing_period_start
        end = request.env.company.billing_period_end
        dates = date_utils.get_billing_start_and_end_dates(date.today(), start, end)
        allowed_reg_date = dates[0].replace(day=int(request.env.company.allowed_reg_date))
        collector_id = self.get_user_partner_id(request.session.uid)
        
        domain = [('name', '=', kw.get("property_id")),
                  ('connection_date', '<=', allowed_reg_date),
                  ('zone_id.collector_id.id', '=', collector_id),
                  ('state', '=', 'connected'),
                  '|', ('meter_type', '!=', 'smart'),
                  '&', ('meter_type', '=', 'smart'),
                        ('auto_reset', '=', True)]
        
        
        property_id = http.request.env['mgs_billing.property'].sudo().search(domain, limit=1)
        
        if not property_id:
            return "Invalid Home Number or Home is not Connected."
        try:
            created_reading = reading_obj.sudo().create({
                'property_id': property_id.id,
                'date': date,
                'current_reading': current_reading,
            })
            created_reading.action_confirm()
            move_id = created_reading.move_id
            result = created_reading.sudo().read(['name', 'move_id', 'date', 'property_id', 'billing_account_id',
                                                  'company_id', 'zone_id', 'last_reading', 'current_reading', 'difference', 'rate', 'amount_total'])
            result[0]['amount_total'] = round(result[0]['amount_total'], 3)

            if property_id.customer_type == 'free':
                result[0].update({
                    'move_id': ['N/A', 'N/A'],
                    'tax_ids': [{}],
                    'service_ids': [{}],
                    'subtotal': 0,
                    'total': 0,
                    'current_balance': 0,
                    'response': 'Success'
                })
                return result

            tax_line_ids = move_id.line_ids.filtered(
                lambda l: 'tax_repartition_line_id' in l.tax_key)
            tax_ids = []
            extra_service_ids = request.env.company.sudo().mgs_extra_service_ids
            service_ids = []
            amount_untaxed = move_id.amount_untaxed
            # --------------------------------
            if len(tax_line_ids) > 0:
                for tax in tax_line_ids:
                    tax_ids.append({
                        'tax_id': tax.tax_line_id.name,
                        'amount': tax.credit
                    })

                result[0].update({
                    'tax_ids': tax_ids
                })

            if len(extra_service_ids) > 0:
                for service in extra_service_ids:
                    service_ids.append({
                        'service_id': service.name,
                        'amount': service.list_price
                    })

                    amount_untaxed -= service.list_price

                result[0].update({
                    'service_ids': service_ids
                })

            result[0].update({
                'subtotal': round(amount_untaxed, 3),
                'total': move_id.amount_total_signed,
                'current_balance': round(self.get_partner_previous_balance(created_reading.billing_account_id.id), 3),
                'response': 'Success'
            })
            if mobile:
                created_reading.billing_account_id.update({'mobile': mobile})
            return result
        except Exception as e:
            return {
                "error": "ERROR: "+str(e),
                'response': 'Fail'
            }