# -*- coding: utf-8 -*-
from odoo import http, fields, api
from odoo.http import request
from datetime import date
import json
from odoo.addons.portal.controllers.portal import pager as portal_pager
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils

import logging

_logger = logging.getLogger(__name__)

class PropertyInfoApi(http.Controller):
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
        date_to = date.today()
        # date_to = dates[1]
        # date_from = date.today().replace(day=request.env.company.billing_period_start)
        # date_to = date.today().replace(
        #     month=next_month, day=request.env.company.billing_period_end)
        allowed_reg_date = False
        if request.env.company.is_allow_reg_date:
            allowed_reg_date = dates[0].replace(day=request.env.company.allowed_reg_date)
            
        
        _from = report_obj._from(date_from, date_to)
        _where = report_obj._where(None, collector_id, None, allowed_reg_date)
        _where += " AND mbp.meter_type != 'smart' "
        return _from+_where

    # def get_billed_unbilled(self, report_type, collector_id):
    #     # query = request.env['mgs.collection.report'].sudo().query_execute(fields.Date.today().replace(day=1), fields.Date.today(), None, collector_id, None)

    #     if 'Dashboard' not in report_type:
    #         select =  "SELECT rp.id as billing_account_id"

    #         request.env.cr.execute(select + self._query_collection())
    #         return request.env.cr.fetchall()

    #     query = query.replace("""SELECT
    #         mbp.id AS id, rp.id AS billing_account_id,
    #         rp.display_name AS display_name, mbp.id AS property_id,
    #         mbp.name AS property_name, mbp.zone_id AS zone_id,
    #         mbz.name AS zone_name, mbp.company_id AS company_id,
    #         COALESCE(sum(CASE WHEN aa.account_type = 'asset_receivable' THEN aml.debit-aml.credit else 0.0 END), 0) balance""", "SELECT COUNT(*)")

    #     request.env.cr.execute(query)
    #     return request.env.cr.fetchone()

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
        start = request.env.company.billing_period_start
        end = request.env.company.billing_period_end
        dates = date_utils.get_billing_start_and_end_dates(date.today(), start, end)
        if date.today() > dates[1]:
            return {
                "response": "Error: Period Time Over"
            }

        
        allowed_reg_date = False
        if request.env.company.is_allow_reg_date:        
            allowed_reg_date = dates[0].replace(
                day=int(request.env.company.allowed_reg_date))

        partner_obj = request.env['res.partner']
        domain = [('property_id.name', '=', kw.get("id").upper()),
                  ('property_id.zone_id.collector_id.id', '=', collector_id), 
                #!  ('property_id.state', '=', 'connected'),
                  ('property_id.meter_type', '!=', 'smart')]
        
        if request.env.company.is_allow_reg_date:
            domain.append(('property_id.connection_date', '<=', allowed_reg_date))
        
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
            "rate": property_id.product_id.lst_price,
            "property_name": property_id.name,
            "property_id": property_id.name,
            "max_above_avg": request.env.company.max_above_avg * avg,
            "max_under_avg": request.env.company.max_under_avg * avg,
            "average_usage": partner_id.average_usage
        }
        _logger.info(self.get_partner_previous_balance(data['partner_id'], " AND aml.date <= '%s'" % date.today()))
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

    @http.route('/billingApi/get_properties_by_number/', type='json', auth='user')
    def get_properties_by_number(self, **kw):     
        data = []   
        owner_number = kw.get("phone_number")        
        partner_obj = request.env['res.partner']  
        #! Removed the property state check from the below condition
        #! ('property_id.state', '=', 'connected'),   
        domain = [('property_id.meter_type', '!=', 'smart'), '|', ('mobile', '=', owner_number),('phone', '=', owner_number)]
        billing_accounts = partner_obj.sudo().search(domain)
        for account in billing_accounts:
            data.append({
                "property_name": account.property_id.name,
                "zone_name": account.property_id.zone_id.name,
                "partner_name": account.name,
                "phone": account.phone,
                'perv_bal': self.get_partner_previous_balance(account.id, " AND aml.date <= '%s'" % date.today()),
            })
        
        return data

    def get_last_reading(self, property_id):
        meter_reading_obj = request.env['mgs_billing.meter.reading']
        property_obj = request.env['mgs_billing.property']
        property_id = property_obj.sudo().search(
            [('name', '=', property_id)], limit=1)
        last_reading = 0
        last_reading = meter_reading_obj.sudo().search(
            [('property_id.id', '=', property_id.id), ('state', '=', 'posted')], limit=1, order='date DESC, id DESC')
        if last_reading:
            last_reading = last_reading.reading_on_date
        else:
            last_reading = property_id.initial_meter
        return last_reading
        # params = [str(property_id)]
        # query = """
        # SELECT mbmreading_on_date,mbmr.property_id
        # FROM mgs_billing_meter_reading mbmr
        # WHERE mbmr.property_id = %s
        # AND mbmr.state = 'posted'
        # ORDER BY mbmr.date, mbmr.id DESC
        # LIMIT 1"""

        # http.request.cr.execute(query, tuple(params))
        # res = http.request.cr.dictfetchall()

        # for r in res:
        #     return r['reading_on_date']

    @http.route('/billingApi/createMeterReading/', type='json', auth='user', methods=['POST'], csrf=False)
    def createMeterReading(self, **kw):        
        request_data = request.httprequest.data
        property_id = kw.get("property_id").upper()
        mobile = kw.get("mobile")
        date = fields.Date().today()
        current_reading = kw.get("current_reading")
        reading_obj = http.request.env['mgs_billing.reading']
        
        start = request.env.company.billing_period_start
        end = request.env.company.billing_period_end
        dates = date_utils.get_billing_start_and_end_dates(date.today(), start, end)
        
        allowed_reg_date = False
        if request.env.company.is_allow_reg_date:        
            allowed_reg_date = dates[0].replace(day=int(request.env.company.allowed_reg_date))
        is_allow_reg_date = request.env.company.is_allow_reg_date
        collector_id = self.get_user_partner_id(request.session.uid)
        
        domain = [('name', '=', kw.get("property_id").upper()),
                  ('zone_id.collector_id.id', '=', collector_id),
                #!  ('state', '=', 'connected'),
                  ('meter_type', '!=', 'smart')]
        
        if is_allow_reg_date:
            domain.append(('connection_date', '<=', allowed_reg_date))
        
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
                                                  'company_id', 'zone_id', 'last_reading', 'current_reading', 'difference', 'rate', 'invoice_amount'])
            result[0]['amount_total'] = round(result[0]['invoice_amount'], 3)
            result[0].update({
                    'collector_number': property_id.zone_id.collector_id.phone,             
                    'collector_name': property_id.zone_id.collector_id.name,         
                })
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
                lambda l: l.tax_repartition_line_id )
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

    @http.route('/billingApi/reprint/', type='json', auth='user', csrf=False)
    def reprint_reading(self, **kw):
        property_id = kw.get("id").upper()
        #! Removed the property state check from the below condition
        #! ('property_id.state', '=', 'connected'),  
        prop_id = http.request.env['mgs_billing.property'].sudo().search(
            [("name", "=", property_id)], limit=1)
        reading = http.request.env['mgs_billing.reading'].sudo().search(
            [('state', '=', 'posted'), ("property_id.name", "=", property_id)], limit=1, order="date DESC, id DESC")
        move_id = reading.move_id
        if reading:
            try:
                result = reading.sudo().read(['name', 'move_id', 'date', 'property_id', 'billing_account_id', 'company_id', 'zone_id', 'last_reading',
                                              'current_reading', 'difference', 'rate', 'invoice_amount'])
                result[0]['amount_total'] = round(result[0]['invoice_amount'], 3)
                result[0].update({
                    'collector_number': prop_id.zone_id.collector_id.phone,                    
                    'collector_name': prop_id.zone_id.collector_id.name,                    
                })
                tax_line_ids = move_id.line_ids.filtered(
                    lambda l: l.tax_repartition_line_id)
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
                    'current_balance':  round(self.get_partner_previous_balance(reading.billing_account_id.id), 3),
                    'status': 'Success'
                })

                return result
            except Exception as e:
                return "ERROR: "+str(e)
        else:
            None
  
    # Prev bal fund
    def get_partner_previous_balance(self, partner_id=None, sub_query=""):
        date_to =  fields.Date.today()
        domain = [
            ('partner_id', '=', partner_id),
            ('parent_state', '=', 'posted'),
            ('date', '<=', date_to),
            ('account_id.account_type', 'in', ['asset_receivable']),
        ]
        aml = request.env['account.move.line'].sudo()
        grouped = aml.read_group(domain, ['debit', 'credit'], [])
        if not grouped:
            return 0.0
        debit = grouped[0].get('debit') or 0.0
        credit = grouped[0].get('credit') or 0.0
        return debit - credit


