# -*- coding: utf-8 -*-

from odoo import http, models, fields, api
from odoo.http import request
from datetime import datetime, date, timedelta
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.mgs_billing.controllers.controllers import PropertyInfoApi as billing_controllers
import json
import werkzeug.wrappers 
import logging
_logger = logging.getLogger(__name__)

class CusomerPortalApi(http.Controller):

    # @http.route('/mgs/spark/usage/', type='http', methods=["GET"], auth='user', csrf=False)
    # def spark_usage_request(self):
    #     data = http.request.httprequest.data
    #     kw = json.loads(data) if data else {}
    #     partner_id = kw.get('partner_id')
    #     user_partner = request.env['res.users'].search([('id', '=', request.session.uid)], limit=1).commercial_partner_id.id
    #     if partner_id != user_partner and self.check_reading_access(user_partner, partner_id) == False:
    #         return werkzeug.wrappers.Response(
    #             status=400,
    #             content_type="application/json; charset=utf-8",
    #             response=json.dumps({"error": "You are not authorized to create this document."}))
    #     partner = request.env['res.partner'].sudo().browse(partner_id)
    #     try:    
    #         property    = partner.property_id
    #         result      = property.sudo()._get_last_spark_reading()
    #         # result      = {"code": 200,"data": "45.89"}
    #         result['data'] = "{:.2f}".format(result['data'])
    #         return werkzeug.wrappers.Response(
    #             status=200,
    #             content_type="application/json; charset=utf-8",
    #             response=json.dumps(result))
    #     except Exception as e:
    #         _logger.error("-=-=-=-=-=-=-=-")
    #         _logger.error(e)
    #         _logger.error("-=-=-=-=-=-=-=-")
    #         return werkzeug.wrappers.Response(
    #             status=400,
    #             content_type="application/json; charset=utf-8",
    #             response=json.dumps({"error": "Something went wrong"}))
    
    
    @http.route('/mgs/helpdesk/create/', type='http', methods=["POST"], auth='user', csrf=False)
    def create_suppprt_request(self):
        data = http.request.httprequest.data
        kw = json.loads(data) if data else {}
        partner_id = kw.get('partner_id')
        user_partner = request.env['res.users'].search([('id', '=', request.session.uid)], limit=1).commercial_partner_id.id
        if partner_id != user_partner and self.check_reading_access(user_partner, partner_id) == False:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                response=json.dumps({"error": "You are not authorized to create this document."}))
        if not kw.get('partner_id',False):
            return werkzeug.wrappers.Response(
                status=401,
                content_type="application/json; charset=utf-8",
                response=json.dumps({"error": "partner_id can not be null."}))
            
        if not kw.get('subject',False):
            return werkzeug.wrappers.Response(
                status=401,
                content_type="application/json; charset=utf-8",
                response=json.dumps({"error": "Please include a subject."}))       
             
        if not kw.get('description',False):
            return werkzeug.wrappers.Response(
                status=401,
                content_type="application/json; charset=utf-8",
                response=json.dumps({"error": "Please include a description."})) 
        
        optional_contact = f"<br/><b>Contact:</b> {kw.get('contact')}" if kw.get('contact') else False
        try:    
            ticket = request.env['helpdesk.ticket'].sudo().create({
                "name" : kw.get('subject'),
                "partner_id" : kw.get('partner_id'),
                "description" : f"{kw.get('description')} {optional_contact if optional_contact else ''}",
            })
            ticket._onchange_partner_id_mgs()
            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                response=json.dumps({"msg":"Sucess", "ticket_ref" : ticket.ticket_ref}))
            
        except Exception as e:
            _logger.error("-=-=-=-=-=-=-=-")
            _logger.error(e)
            _logger.error("-=-=-=-=-=-=-=-")
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                response=json.dumps({"error": "Something went wrong"}))
    
    @http.route('/mgs/helpdesk/status/', type='json', methods=["GET"], auth='user', csrf=False)
    def get_suppprt_status(self, **kw):
        data = http.request.httprequest.data
        partner_id = kw.get('partner_id')
        user_partner = request.env['res.users'].search([('id', '=', request.session.uid)], limit=1).commercial_partner_id.id
        if partner_id != user_partner and self.check_reading_access(user_partner, partner_id) == False:
            return {"error": "You are not authorized to create this document."}
        if not kw.get('partner_id',False):
            return {"error": "partner_id can not be null."}
            
        domain = [('partner_id.id', '=', partner_id )]
        tickets_count = request.env['helpdesk.ticket'].sudo().search_count(domain)
        limit = 10
        pager = portal_pager(
            url="/mgs/helpdesk/status/",
            url_args={'date_begin': None,
                      'date_end': None, 'sortby': 'date DESC'},
            total=tickets_count,
            page=kw.get('page') or 1,
            step=limit)
        
        tickets = request.env['helpdesk.ticket'].sudo().search(domain, limit=limit, order='create_date DESC, id DESC', offset=pager['offset'])
        
        lines = [{
            "name": x.name or "",
            "create_date": x.create_date or "",
            "technician": x.user_id.name or "",
            "status": x.stage_id.name or "",
        } for x in tickets]
        
        
        return {
            'lines': lines,
            'pages': pager['page_count']
        }
        
    
    @http.route('/mgs/customer/payments/', type='json', auth='user')
    def get_payments(self, **kw):
        partner_id = kw.get('partner_id')
        user_partner = request.env['res.users'].search(
            [('id', '=', request.session.uid)], limit=1).commercial_partner_id.id
        if not partner_id:
            return "No partner specified"
        if partner_id != user_partner and self.check_reading_access(user_partner, partner_id) == False:
            return "You are not authorized to view these documents"
        domain = [('partner_id.id', '=', partner_id),
                  ('payment_type', '=', 'inbound'), ('state', '=', 'posted')]
        am_counter = request.env['account.payment'].sudo().search_count(domain)
        limit = 10
        pager = portal_pager(
            url="/mgs/customer/payments/",
            url_args={'date_begin': None,
                      'date_end': None, 'sortby': 'date DESC'},
            total=am_counter,
            page=kw.get('page') or 1,
            step=limit)
        lines = request.env['account.payment'].sudo().search(
            domain, limit=limit, order='date DESC, id DESC', offset=pager['offset']).read(['date', 'name', 'ref', 'amount'])
        return {
            'lines': lines,
            'pages': pager['page_count']
        }

        # return request.env['account.payment'].sudo().search(domain, limit=limit, order='date DESC, id DESC', offset=pager['offset']).read(['date', 'name', 'ref', 'amount'])

    @http.route('/mgs/customer/invoices/', type='json', auth='user')
    def get_invoices(self, **kw):
        partner_id = kw.get('partner_id')
        user_partner = request.env['res.users'].search(
            [('id', '=', request.session.uid)], limit=1).commercial_partner_id.id
        if not partner_id:
            return "No partner specified"
        if partner_id != user_partner and self.check_reading_access(user_partner, partner_id) == False:
            return "You are not authorized to view these documents"
        domain = [('partner_id.id', '=', partner_id), ('move_type',
                                                       '=', 'out_invoice'), ('state', '=', 'posted')]
        am_counter = request.env['account.move'].sudo().search_count(domain)
        limit = 10
        pager = portal_pager(
            url="/mgs/customer/invoices/",
            url_args={'date_begin': None,
                      'date_end': None, 'sortby': 'date DESC'},
            total=am_counter,
            page=kw.get('page') or 1,
            step=limit)
        lines = []
        moves = request.env['account.move'].sudo().search(domain, limit=limit, order='date DESC,id DESC', offset=pager['offset'])
        
        for move in moves:
            lines.append({
                'date': move.date,
                'name': move.name,
                'ref':move.ref,
                'amount_total':move.amount_total,
                "description":f"Aqris Danbe: {round(move.reading_id.current_reading, 2)} - Aqris Hore: {round(move.reading_id.last_reading, 2)} = Isticmaalka: {round(move.reading_id.difference, 2)}" if move.reading_id else move.name,
            })
        return {
            'lines': lines,
            'pages': pager['page_count']
        }

    @http.route('/mgs/customer/accounts/', type='json', auth='user')
    def get_allowed_partners_api(self, **kw):
        lines = self.get_allowed_partners(request.env['res.users'].search(
            [('id', '=', request.session.uid)], limit=1).commercial_partner_id.id).read(['id', 'name', 'mgs_credit'])
        am_counter = len(lines)  # FIXME
        limit = 10
        pager = portal_pager(
            url="/mgs/customer/accounts/",
            url_args={'date_begin': None,
                      'date_end': None, 'sortby': 'date DESC'},
            total=am_counter,
            page=kw.get('page') or 1,
            step=limit)
        return {
            'lines': lines,
            'pages': pager['page_count']
        }

    @http.route('/mgs/customer/open/move/', type='json', auth='user')
    def open_move(self, **kw):
        move_id = request.env['account.move'].sudo().search(
            [('name', '=', kw.get('name'))])
        if move_id:
            user_partner = request.env['res.users'].search(
                [('id', '=', request.session.uid)], limit=1).commercial_partner_id.id
            if move_id.partner_id.id not in self.get_allowed_partners(user_partner).ids:
                return "You are not allowed to view this document"
            if kw.get('payment_id') and move_id.move_type == 'entry':
                return move_id.line_ids.filtered(lambda x: x.credit != 0.0).read(['name', 'mgs_credit'])
            # FIXME
            return move_id.invoice_line_ids.read(['name', 'quantity', 'price_unit', 'price_subtotal'])
        # return {
        #     'lines': lines,
        #     'pages': pager['page_count']
        # }

    def _generate_options(self, report, date_from, date_to, default_options=None):
        if isinstance(date_from, datetime):
            date_from_str = fields.Date.to_string(date_from)
        else:
            date_from_str = date_from
        if isinstance(date_to, datetime):
            date_to_str = fields.Date.to_string(date_to)
        else:
            date_to_str = date_to
        if not default_options:
            default_options = {}
        return report.sudo()._get_options({
            'report_id': report.id,
            'date': {
                'date_from': date_from_str,
                'date_to': date_to_str,
                'mode': 'range',
                'filter': 'custom',
            },
            **default_options,
        })

    def get_allowed_partners(self, partner_id):
        return request.env['res.partner'].sudo().search(['|', ('message_partner_ids', 'child_of', (partner_id)), ('id', '=', partner_id)])

    def check_reading_access(self, user_partner, partner_id):
        allowed_partner_ids = self.get_allowed_partners(user_partner)
        if not allowed_partner_ids:
            return False
        elif partner_id not in allowed_partner_ids.ids:
            return False
        return True

    @http.route('/mgs/customer/statement/', type='json', auth='user')
    def get_statement(self, **kw):
        partner_id = kw.get('partner_id')
        user_partner = request.env['res.users'].search(
            [('id', '=', request.session.uid)], limit=1).commercial_partner_id.id
        if not partner_id:
            return "No partner specified"
        if partner_id != user_partner and self.check_reading_access(user_partner, partner_id) == False:
            return "You are not authorized to view these documents"
        date = fields.Date.today()  # default date
        date_from = kw.get('date_from') or date.replace(day=1)
        date_to = kw.get('date_to') or date
        options = self._generate_options(request.env.ref(
            'account_reports.partner_ledger_report'), date_from, date_to)
        # aml_counter = request.env['account.move.line'].sudo().search_count([
        #     ('partner_id', '=', partner_id),
        #     ('account_id.account_type', 'in', (
        #         'asset_receivable', 'liability_payable'))
        # ])
        limit   = 30
        page    = kw.get('page') or 1
        report_obj = request.env['mgs.account.partner.ledger.report.handler']
        
        lines   = report_obj.sudo()._get_mgs_aml_values(
            options,  # _get_aml_values required parameter
            [partner_id],  # partner_ids list
            int(page - 1),  # pager
            limit  # limit = 30
        )
        pager   = portal_pager(
            url="/mgs/customer/statement/",
            url_args={'date_begin': None,'date_end': None, 'sortby': 'date'},
            total=len(lines),
            page=page,
            step=limit)
        
        

        new_date_to = fields.Date.from_string(date_to) + timedelta(days=1)
        balance_options = self._generate_options(request.env.ref('account_reports.partner_ledger_report'), new_date_to, new_date_to)
        return {
            'initial_balances'  : report_obj.sudo()._get_initial_balance_values(partner_id, options) or 0.0,
            'balance'           : report_obj.sudo()._get_initial_balance_values(partner_id, balance_options) or 0.0,
            'lines'             : lines,
            'pages'             : pager['page_count']
        }
        
    @http.route('/mgs/customer/payment_provider/', type='json', auth='user')
    def get_payment_providers(self, **kw):
        partner_id = kw.get('partner_id')
        user_partner = request.env['res.users'].search([('id', '=', request.session.uid)], limit=1).commercial_partner_id.id
        if partner_id != user_partner and self.check_reading_access(user_partner, partner_id) == False:
            return {"error": "You are not authorized to create this document."}
        if not kw.get('partner_id',False):
            return {"error": "partner_id can not be null."}
            
            
        
        providers = request.env['payment.provider'].sudo().search([('available_on_mobile_app', "=", True)]).read(['id', 'name'])
        limit = 10
        page    = kw.get('page') or 1
        
        
        pager   = portal_pager(
            url="/mgs/customer/payment_provider/",
            url_args={'date_begin': None,'date_end': None, 'sortby': 'date'},
            total=len(providers),
            page=page,
            step=limit)
        
        return {
            'status': 200,
            "providers": providers, 
            'pages' : pager['page_count']
        }
            
    def clean_number(self, number):
        if number.startswith("+"):
            number = number[1:]
        number = number.replace(" ", "")
        return number
    
    @http.route('/mgs/customer/numbers/', type='json', auth='user')
    def get_payment_provider(self, **kw):
        partner_id = kw.get('partner_id')
        user_partner = request.env['res.users'].search([('id', '=', request.session.uid)], limit=1).commercial_partner_id.id
        if partner_id != user_partner and self.check_reading_access(user_partner, partner_id) == False:
            return {"error": "You are not authorized to create this document."}
        if not kw.get('partner_id',False):
            return {"error": "partner_id can not be null."}
            
            
        
        vals = []
        numbers = request.env['res.partner'].sudo().search([('id', "=", partner_id)], limit=1)
        
        

        if numbers.phone:
            vals.append(self.clean_number(numbers.phone))
        if numbers.mobile:
            vals.append(self.clean_number(numbers.mobile))
        if numbers.alternative_number:
            vals.append(self.clean_number(numbers.alternative_number))
        
        return {
            'status': 200,
            "numbers": vals, 
        }
            
        
        