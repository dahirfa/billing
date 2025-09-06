# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import pytz


class MgsPayment(models.Model):
    _inherit = 'mgs.payment.transaction'
    _description = 'MGS Payment'
    _order = 'id desc'

    sender_account = fields.Char(tracking=True)
    # is_prepaid = fields.Boolean(tracking=True)
    meter_no = fields.Char(tracking=True)

    
    @api.model_create_multi
    def create(self, vals_list):
        res = super(MgsPayment, self).create(vals_list)
        records = res.filtered(lambda x: x.method_code == 'sahal_sc' and x.state not in ('cancel', 'duplicate'))
        records.filtered(lambda x: not x.partner_id).action_sahal_sc_draft()
        records.filtered(lambda x: x.partner_id).action_sahal_sc_confirm()
        return res

    def action_sahal_sc_draft(self):
        payment_obj = self.env['account.payment']
        payment_method_line_id = self.env.ref(
            'mgs_sahal_integration.payment_method_sahal_sc')

        mgs_unknown_partner_id_obj = self.env.company.mgs_unknown_partner_id
        if not payment_method_line_id:
            raise ValidationError(
                "No Payment method was found for this provider")

        if not mgs_unknown_partner_id_obj:
            raise ValidationError(
                "Please set a dummy partner to store  all payments with unknown sources")
        unknown_partner_id = mgs_unknown_partner_id_obj
        for payment in self:
            payments = payment.payment_ids
            payments.payment_ids.with_context(allow_action=True).action_draft()
            payments.payment_ids.unlink()
            vals = payment._prepare_payment_vals(
                payment_method_line_id.id, unknown_partner_id)
            new_payment = payment_obj.create(vals)
            new_payment.with_context(allow_action=True).action_post()
            payment.payment_id = new_payment.id
            payment._set_draft()
        return

    def action_sahal_sc_confirm(self):
        payment_obj = self.env['account.payment']
        payment_method_line_id = self.env.ref('mgs_sahal_integration.payment_method_sahal_sc')
        for payment in self.filtered(lambda x: x.state not in ('cancel', 'duplicate')):
            payment_id = payment.payment_id
            if not payment.partner_id and not payment.breakdown:
                raise ValidationError("Select A partner")
            if not payment.breakdown:
                vals = payment._prepare_payment_vals(
                    payment_method_line_id.id, payment.partner_id)
                if not payment_id:
                    new_payment = payment_obj.create(vals)
                    payment_id = new_payment
                    payment.payment_id = new_payment.id
                else:
                    payment_id.with_context(allow_action=True).action_draft()
                    payment_id.write(vals)
                payment_id.with_context(allow_action=True).action_post()
                payment._set_confirm()

            else:
                if len(payment.line_ids) == 0:
                    raise ValidationError("Please breakdown the payment first")
                break_down_total = sum(payment.line_ids.mapped('amount'))
                amount = payment.amount
                if break_down_total != amount:
                    raise ValidationError(
                        "Amount must be equal to the total amount")
                if payment_id:
                    payment_id.with_context(allow_action=True).action_draft()
                    payment_id.unlink()
                for line in payment.line_ids:
                    journal = payment.journal_id
                    vals = line._prepare_payment(
                        journal.id, payment.name, payment.paid_by, payment.date)
                    vals.update({'mgs_p_transaction_id': payment.id, 'payment_method_line_id': journal.inbound_payment_method_line_ids.filtered(
                        lambda x: x.payment_method_id.id == payment_method_line_id.id).id})
                    existing_pay = line.payment_id
                    if existing_pay:
                        existing_pay.with_context(
                            allow_action=True).action_draft()
                        existing_pay.write(vals)
                        self.env.cr.commit()
                        existing_pay.with_context(
                            allow_action=True).action_post()
                    else:
                        new_payment = payment_obj.create(vals)
                        self.env.cr.commit()
                        new_payment.with_context(
                            allow_action=True).action_post()
                        line.payment_id = new_payment.id
                payment._set_confirm()

    # def _prepare_payment_vals(self, payment_method_line_id, partner_id):
    #     journal_id = self.journal_id
    #     method_line_id = journal_id.inbound_payment_method_line_ids.filtered(
    #         lambda x: x.payment_method_id.id == payment_method_line_id)
    #     target_timezone = pytz.timezone('Africa/Mogadishu')
    #     date = self.date.astimezone(target_timezone)
    #     return {
    #         'mgs_p_transaction_id':     self.id,
    #         'partner_id':               partner_id,
    #         'amount':                   self.amount,
    #         'date':                     date,
    #         'journal_id':               journal_id.id,
    #         'payment_method_line_id':   method_line_id.id,
    #         'mgs_transaction_ref':      self.name,
    #         'mgs_sender_phone':         self.paid_by,
    #         'payment_type':             'inbound'
    #     }


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[(
        'sahal_sc', "Golis-Short-Code")], ondelete={'sahal_sc': 'set default'})

    sahal_sc_user_id = fields.Many2one('res.users', domain =[('share','=',True)])
    # sahal_api_password = fields.Char()


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['sahal_sc'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        return res
