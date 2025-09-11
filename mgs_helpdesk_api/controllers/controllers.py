# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import pager as portal_pager


class MgsHelpdeskApi(http.Controller):
    @http.route('/helpdeskapi/tickets/', auth='user', type='json')
    def get_tickets(self, **kw):
        domain = [('user_id.id', '=', kw.get('user_id')),
                  ('stage_name', '=', kw.get('stage'))]
        ticket_obj = http.request.env['helpdesk.ticket']
        ticket_count = ticket_obj.sudo().search_count(domain)
        limit = 100
        page = kw.get('page') if kw.get('page') else 1
        pager = portal_pager(
            url="/helpdeskapi/tickets/",
            url_args={'date_begin': None, 'date_end': None, 'sortby': None},
            total=ticket_count,
            page=page,
            step=limit
        )
        tickets = ticket_obj.sudo().search(domain, limit=limit, order='priority DESC,id DESC', offset=pager['offset']).read(
            ['id', 'name', 'create_date', 'description', 'priority', 'priority_name', 'stage_name', 'partner_name', 'partner_phone', 'zone_id'])
        return tickets

    @http.route('/helpdeskapi/search_ticket', auth='user', type='json')
    def get_ticket(self, **kw):
        ticket_obj = http.request.env['helpdesk.ticket'].sudo().search([('id', '=', kw.get('ticket_id'))], limit=1).read(
            ['id', 'name', 'description', 'priority', 'priority_name', 'stage_name', 'partner_name', 'partner_phone', 'zone_id', 'street', 'street2'])
        return ticket_obj

    @http.route('/helpdeskapi/dashboard', auth='user', type='json')
    def dashboard(self, **kw):
        stage_obj = http.request.env['helpdesk.stage'].sudo().search(
            [('active', '=', True)]).read(['id', 'name'])
        dashboard = {}
        for stage in stage_obj:
            counter = http.request.env['helpdesk.ticket'].sudo().search_count(
                [('user_id.id', '=', kw.get('user_id')), ('stage_id.id', '=', stage['id'])])
            dashboard[stage['name']] = counter
        return dashboard

    @http.route('/helpdeskapi/get_ticket_stages', auth='user', type='json')
    def get_in_progrss(self, **kw):
        stage_obj = http.request.env['helpdesk.stage'].sudo().search(
            [('active', '=', True)]).mapped('name')
        print(stage_obj)
        return stage_obj

    @http.route('/helpdeskapi/start_ticket', auth='user', type='json')
    def start_task(self, **kw):
        ticket_obj = http.request.env['helpdesk.ticket'].sudo().search(
            [('id', '=', int(kw.get('ticket_id')))])
        in_progress_stage = int(http.request.env['ir.config_parameter'].sudo(
        ).get_param('mgs_helpdesk_api.in_progress_stage_id'))
        try:
            ticket_obj.stage_id = in_progress_stage
        except Exception as e:
            return str(e)
        return "success"

    @http.route('/helpdeskapi/suspend_ticket', auth='user', type='json')
    def suspended_task(self, **kw):
        ticket_obj = http.request.env['helpdesk.ticket'].sudo().search(
            [('id', '=', int(kw.get('ticket_id')))])
        suspended_stage = int(http.request.env['ir.config_parameter'].sudo(
        ).get_param('mgs_helpdesk_api.suspended_stage_id'))
        try:
            ticket_obj.stage_id = suspended_stage
        except Exception as e:
            return str(e)
        return "success"

    @http.route('/helpdeskapi/finish_ticket', auth='user', type='json')
    def finish_task(self, **kw):
        ticket_obj = http.request.env['helpdesk.ticket'].sudo().search(
            [('id', '=', int(kw.get('ticket_id')))])
        to_review_stage_id = int(http.request.env['ir.config_parameter'].sudo(
        ).get_param('mgs_helpdesk_api.to_review_stage_id'))
        try:
            ticket_obj.stage_id = to_review_stage_id
            ticket_obj.message_post(body=" ".join(
                ("Comment :", str(kw.get('comments')))))
        except Exception as e:
            return str(e)
        return "success"

    @http.route('/helpdeskapi/cancel_ticket', auth='user', type='json')
    def cancel_task(self, **kw):
        ticket_obj = http.request.env['helpdesk.ticket'].sudo().search(
            [('id', '=', int(kw.get('ticket_id')))])
        cancel_stage_id = int(http.request.env['ir.config_parameter'].sudo(
        ).get_param('mgs_helpdesk_api.cancel_stage_id'))
        try:
            ticket_obj.stage_id = cancel_stage_id
            ticket_obj.message_post(body=" ".join(
                ("Canceling reason :", str(kw.get('canceling_reason')))))
        except Exception as e:
            return str(e)
        return "success"
