# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import re
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)
import pytz


class MgsPaymentLineInherit(models.Model):
    _inherit = 'mgs.payment.line'
    mgs_sahal_im_line_id = fields.Many2one(
        'mgs.golis.sahal.payment', string='Sahal Statement Line')


class PaymentInheritMgs(models.Model):
    _inherit = 'account.payment'

    mgs_sahal_im_line_id = fields.Many2one(
        'mgs.golis.sahal.payment', string='Sahal Statement Line')

    def action_draft(self):
        for r in self:
            if self.env.user.has_group('base.group_system'):
                return super(PaymentInheritMgs, self).action_draft()
            if r.mgs_sahal_im_line_id and 'allow_action' not in self.env.context:
                raise UserError("Action not allowed!")
        return super(PaymentInheritMgs, self).action_draft()

    def action_cancel(self):
        for r in self:
            if self.env.user.has_group('base.group_system'):
                return super(PaymentInheritMgs, self).action_cancel()
            if r.mgs_sahal_im_line_id and 'allow_action' not in self.env.context:
                raise UserError("Action not allowed!")
        return super(PaymentInheritMgs, self).action_cancel()

    def action_post(self):
        for r in self:
            if self.env.user.has_group('base.group_system'):
                return super(PaymentInheritMgs, self).action_post()
            if r.mgs_sahal_im_line_id and 'allow_action' not in self.env.context:
                raise UserError("Action not allowed!")
        return super(PaymentInheritMgs, self).action_post()


class MgsGolisPayment(models.Model):
    _name = 'mgs.golis.sahal.payment'
    _description = "Sahal Payment"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'mgs.payment.base']
    _rec_name = 'transactionid'
    _order = 'id DESC'

    # Base Fields
    transactionid = fields.Char(string="TRANSFERID", tracking=True)
    description = fields.Char(string="DESCRIPTION", tracking=True)
    otherpartyaccount = fields.Char(string="OTHERPARTYACCOUNT", tracking=True)
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    debit = fields.Char(string="DEBIT", tracking=True)
    credit = fields.Char(string="CREDIT", tracking=True)
    amount = fields.Monetary(compute='compute_amount',
                             tracking=True, store=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain=[
                                 ('type', '=', 'bank')], tracking=True, check_company=True)
    balance = fields.Float(string="BALANCE", tracking=True)
    transferdate = fields.Datetime(string="TRANSFERDATE", tracking=True)
    payment_id = fields.Many2one('account.payment', tracking=True)

    payment_ids = fields.One2many(
        'account.payment', 'mgs_sahal_im_line_id', tracking=True)
    line_ids = fields.One2many(
        'mgs.payment.line', 'mgs_sahal_im_line_id', tracking=True)
    payment_count = fields.Integer(
        compute='_count_paments', string="Payment", tracking=True)
    active = fields.Boolean(default=True, ondelete='restrict', tracking=True)
    # Computed Fields
    transaction_mobile = fields.Char(
        string="Sender Mobile",  store=True, tracking=True, compute="_extract_from_description")
    meter_no = fields.Char(string="Meter #",  store=True,
                           tracking=True, compute="_extract_from_description")
    partner_id = fields.Many2one('res.partner', store=True, readonly=False,
                                 tracking=True, compute='_get_partner', string="Billing Account")
    state = fields.Selection([('duplicate', 'Duplicate'), ('invalid', 'Invalid'), (
        'draft', 'To Confirm'), ('confirm', 'Confirmed')], tracking=True)
    error_msg = fields.Char()

    @api.depends('payment_ids')
    def _count_paments(self):
        for r in self:
            r.payment_count = len(r.payment_ids)

    def unlink(self):
        with_payment = self.filtered(lambda x: x.payment_id)
        if with_payment:
            raise ValidationError('You cannot unlink this record')
        res = super(MgsGolisPayment, self).unlink()
        return res

    @api.depends('meter_no', 'transaction_mobile')
    def _get_partner(self):
        # rp_obj = self.env['res.partner']
        for payment in self:
            payment.partner_id = None
            if payment.transaction_mobile and payment.meter_no:
                query = """ SELECT rp.id
                            FROM res_partner rp
                            LEFT JOIN mgs_billing_property mbp ON mbp.id =  rp.property_id
                            WHERE (REPLACE(REPLACE(rp.mobile, ' ', ''), '+', '') = %s)
                            AND  mbp.name = %s """
                self.env.cr.execute(
                    query, (payment.transaction_mobile, payment.meter_no))
                partners = self.env.cr.dictfetchall()
                # partner = rp_obj.search(['|', ('property_id.name', '=', payment.meter_no), ('mobile', '!=', False), ('mobile', '=', payment.transaction_mobile)])
                if len(partners) == 1:
                    payment.partner_id = partners[0]['id']
                elif len(partners) > 1:
                    payment.error_msg = "Multiple Accounts"

    @api.onchange('breakdown')
    def onchange_breakdown(self):
        if self.state != 'confirm':
            self.partner_id = None
            self.line_ids = None

    @api.depends('credit')
    def compute_amount(self):
        for r in self:
            if r.credit != '-':
                try:
                    r.amount = float(r.credit)
                except ValueError:
                    r.amount = 0.0
            else:
                r.amount = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        mpt = self.env['mgs.payment.transaction']
        ap = self.env['account.payment']
        for vals in vals_list:
            transactionid = vals.get('transactionid')
            if mpt.search_count([('name', '=', transactionid)]) or self.search_count([('transactionid', '=', transactionid)]) or ap.search_count([('mgs_transaction_ref', '=', transactionid)]):
                vals['state'] = 'duplicate'
                vals['active'] = False
            if vals['debit'] != '-' or float(vals['credit']) <= 0.0:
                vals['state'] = 'invalid'
                vals['active'] = False
        res = super(MgsGolisPayment, self).create(vals_list)
        records = res.filtered(
            lambda x: x.state not in ('invalid', 'duplicate'))
        records.filtered(lambda x: not x.partner_id).action_draft()
        records.filtered(lambda x: x.partner_id).action_confirm()
        return res

    def cron_clean_transactions(self):
        mpt = self.env['mgs.payment.transaction'].filtered(
            lambda x: x.state in ('duplicate')).unlink()
        mgsp = self.env['mgs.golis.sahal.payment'].filtered(
            lambda x: x.state in ('invalid', 'duplicate')).unlink()

    def action_draft(self):
        payment_obj = self.env['account.payment']
        mgs_unknown_partner_id_obj = self.env.company.mgs_unknown_partner_id
        if not mgs_unknown_partner_id_obj:
            raise ValidationError(
                "Please set a dummy partner to store  all payments with unknown sources")
        unknown_partner_id = mgs_unknown_partner_id_obj
        for payment in self:
            if payment.state in ('invalid', 'duplicate'):
                raise ValidationError(
                    "You van confirm or set to draft invalid or duplicate entries")
            journal_id = payment.journal_id
            payments = payment.payment_ids
            if payments:
                payments.payment_ids.with_context(
                    allow_action=True).action_draft()
                payments.payment_ids.unlink()
            vals = payment._prepare_payment_vals(
                journal_id.id, unknown_partner_id)
            new_payment = payment_obj.create(vals)
            new_payment.with_context(allow_action=True).action_post()
            payment.payment_id = new_payment.id
            payment.write({'state': 'draft'})

    # @api.onchange('partner_id')
    # def _onchange_partner(self):
    #     if self.partner_id and self.partner_id.property_id.name != self.meter_no:
    #         return {
    #             'warning': {
    #                 'title': _("Unmatching meter #"),
    #                 'message': _("The customer's meter # does not match the meter # in the payment."
    #                                 "ss")}}

    def action_confirm(self):
        payment_obj = self.env['account.payment']
        for payment in self.filtered(lambda x: x.state not in ('invalid', 'duplicate')):
            if payment.state in ('invalid', 'duplicate'):
                raise ValidationError(
                    "You van confirm or set to draft invalid or duplicate entries")
            journal_id = payment.journal_id
            if not payment.partner_id and payment.breakdown == False:
                raise ValidationError("Select a partner")
            if payment.state == 'confirm':
                raise ValidationError("This record is already confirmed")
            vals = payment._prepare_payment_vals(
                journal_id.id, payment.partner_id)
            existing_pay = payment.payment_id
            if payment.breakdown == False:
                if existing_pay:
                    existing_pay.with_context(allow_action=True).action_draft()
                    existing_pay.write(vals)
                    existing_pay.with_context(allow_action=True).action_post()
                else:
                    new_payment = payment_obj.create(vals)
                    new_payment.with_context(allow_action=True).action_post()
                    payment.payment_id = new_payment.id
                payment.state = 'confirm'
            else:
                if len(payment.line_ids) == 0:
                    raise ValidationError("Please breakdown the payment first")
                break_down_total = sum(payment.line_ids.mapped('amount'))
                amount = payment.amount
                if round(break_down_total, 2) != round(amount, 2):
                    raise ValidationError(
                        "Amount must be equal to the total amount")
                if existing_pay:
                    existing_pay.with_context(allow_action=True).action_draft()
                    existing_pay.unlink()
                for line in payment.line_ids:
                    vals = line._prepare_payment(
                        journal_id.id, payment.transactionid, payment.transaction_mobile, payment.transferdate)
                    vals.update({'mgs_sahal_im_line_id': payment.id})
                    l_existing_pay = line.payment_id
                    if l_existing_pay:
                        l_existing_pay.with_context(allow_action=True).action_draft()
                        l_existing_pay.write(vals)
                        self.env.cr.commit()
                        l_existing_pay.with_context(allow_action=True).action_post()
                    else:
                        new_payment = payment_obj.create(vals)
                        self.env.cr.commit()
                        new_payment.with_context(allow_action=True).action_post()
                        line.payment_id = new_payment.id
                payment.state = 'confirm'

    def _prepare_payment_vals(self, journal_id, partner_id):
        target_timezone = pytz.timezone('Africa/Mogadishu')
        date = self.transferdate.astimezone(target_timezone)
        return {
            'mgs_sahal_im_line_id': self.id,
            'partner_id':           partner_id.id,
            'amount':               float(self.credit),
            'date':                 date,
            'mgs_transaction_ref':  self.transactionid,
            'mgs_sender_phone':     self.transaction_mobile,
            'journal_id':           journal_id,
            'payment_type':         'inbound',
        }

    def action_view_payments(self):
        payments = self.mapped('payment_ids')
        action = self.env.ref(
            'account.action_account_payments').sudo().read()[0]
        if len(payments) > 1:
            action['domain'] = [('id', 'in', payments.ids)]
        elif len(payments) == 1:
            action['views'] = [
                (self.env.ref('account.view_account_payment_form').id, 'form')]
            action['res_id'] = payments.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.depends('description')
    def _extract_from_description(self):
        for payment in self:
            string = payment.description or ""

            # Extract phone number
            phone_regex = r"\d{12}"
            phone_match = re.search(phone_regex, string)
            phone = phone_match.group() if phone_match else None

            payment.transaction_mobile = phone

            # Extract invoice number
            invoice_regex = r"Invoice No: (\d+)"
            invoice_match = re.search(invoice_regex, string)
            meter_no = invoice_match.group(1) if invoice_match else None
            # if meter_no and len(meter_no) <= 4:
            #     meter_no = meter_no.zfill(5)
            payment.meter_no = meter_no
