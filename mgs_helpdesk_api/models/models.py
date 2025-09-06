# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError


class InheritHelpDeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    stage_name = fields.Char(related='stage_id.name')
    priority_name = fields.Char(
        string='Priority Name', compute='_compute_priority_name')
    zone_id = fields.Char(string='Zone')
    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)

    def action_send_sms_technician(self):
        mgs_sms_obj = self.env['mgs.sms']
        model_obj = self.env['ir.model'].sudo().search(
            [('model', '=', self._inherit)]).id
        partner_id = self.user_id.partner_id
        user_mobile = partner_id.mobile.replace(" ", "")

        if not user_mobile:
            raise UserError(
                "Please define a number for this user")

        if '+' in user_mobile:
            user_mobile = user_mobile.replace('+', '')

        if not self.user_id.id:
            raise UserError(
                "You must assign a user to this task in order to send an SMS")
            # partner_balance = str(partner_id.credit)
        msg = """Mudane %s Waxaa laguu asteeyay shaqadan:
Macamiil: %s
Nooca shaqada: %s. Saacad: %s. Zone: %s. Aaga: %s. Mob: %s """ % (
            self.user_id.name, self.partner_id.name, self.ticket_type_id.name or '/', self.partner_id.property_id.name, self.zone_id, self.street, self.partner_phone)
        sms_record = mgs_sms_obj.create({'source_name': self.name, 'message': msg, 'mobile': user_mobile,
                                         'partner_id': partner_id.id, 'model_id': model_obj, 'datetime': datetime.now()})
        if sms_record:
            try:
                response = sms_record.action_send_sms()
                self.message_post(body=response)
            except Exception as e:
                sms_record.message_post(body=str(e))

    def action_send_sms_customer(self):
        mgs_sms_obj = self.env['mgs.sms']
        model_obj = self.env['ir.model'].sudo().search(
            [('model', '=', self._inherit)]).id
        partner_id = self.user_id.partner_id
        user_mobile = partner_id.mobile.replace(" ", "")

        partner_name = self.partner_id.name if self.partner_id else self.name

        if not self.user_id.id:
            raise UserError(
                "You must assign a user to this task in order to send an SMS")

        if not user_mobile:
            raise UserError(
                "Please define a number for this user")

        if '+' in user_mobile:
            user_mobile = user_mobile.replace('+', '')

        partner_phone = self.partner_phone

        if not partner_phone:
            raise UserError(
                "Please define a customer number for this ticket")

        if '+' in partner_phone:
            partner_phone = user_mobile.replace('+', '')
            # partner_balance = str(partner_id.credit)
        msg = "Macmiil: %s Shaqadaadii waxaa loo asteeyey %s Kala xiriir: %s Mahadsanid" % (
            partner_name, partner_id.name, user_mobile)
        sms_record = mgs_sms_obj.create({'source_name': self.name, 'message': msg, 'mobile': partner_phone,
                                         'partner_id': partner_id.id, 'model_id': model_obj, 'datetime': datetime.now()})
        if sms_record:
            try:
                response = sms_record.action_send_sms()
                self.message_post(body=response)
            except Exception as e:
                sms_record.message_post(body=str(e))

    def action_send_sms(self):
        self.action_send_sms_technician()
        self.action_send_sms_customer()

    @api.onchange('partner_id')
    def _onchange_partner_id_mgs(self):
        self.zone_id = None
        self.street = None
        self.street2 = None
        self.partner_phone = False
        self.partner_phone = self.partner_id.mobile
        if self.partner_id.property_id:
            self.zone_id = self.partner_id.property_id.zone_id.name if self.partner_id.property_id.zone_id else None
            self.street = self.partner_id.street
            self.street2 = self.partner_id.street2

    @api.depends('priority')
    def _compute_priority_name(self):
        for r in self:
            selection_obj = self.env['ir.model.fields.selection']
            domain = [('field_id.name', 'like', 'priority'),
                      ('field_id.model_id.model', '=', self._name), ('value', '=', r.priority)]
            r.priority_name = selection_obj.search(domain).name
