# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
import qrcode
import base64
from io import BytesIO
import logging
_logger = logging.getLogger(__name__)


class InheritHelpDeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    stage_name = fields.Char(related='stage_id.name')
    
    priority_name = fields.Char(string='Priority Name', compute='_compute_priority_name')
    
    zone_id = fields.Many2one('mgs_billing.zone', related='partner_id.zone_id', store=True)
    
    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)
    
    #! NEW CHANGES TO HELPDESK MODEL
    before_work_start_image = fields.Html(string="Before Work Starts")
    before_work_start_image_base64 = fields.Char(string="Before Work Starts Base 64 Format")
    after_work_end_image = fields.Html(string="After Work Ends")
    after_work_end_image_base64 = fields.Char(string="After Work Ends Base 64 Format")
    prework_lat = fields.Char(string="Pre Work Lat")
    prework_lon = fields.Char(string="Pre Work Lon")
    post_work_lat = fields.Char(string="Post Work Lat")
    post_work_lon = fields.Char(string="Post Work Lon")
    qr_code = fields.Char(string="QR Data", tracking=True)
    qr_image = fields.Binary(string="QR Code", compute="generate_qr_code")
    accepted_rejected_state = fields.Selection(string="Accepted/Rejected", selection=[("rejected", "Rejected"), ("accepted", "Accepted")], tracking=True)
    reject_reason = fields.Char(string="Reason for Rejection", tracking=True)
    
    
    def generate_qr_code(self):
        for rec in self:
            if rec.qr_code:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=3,
                    border=4,
                )            
                qr.add_data(rec.qr_code)            
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.update({'qr_image': qr_image})
            else:
                rec.qr_image = False
    
    

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
            Nooca shaqada: %s. Saacad: %s. Zone: %s. Aaga: %s. Mob: %s 
        """ % (
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
