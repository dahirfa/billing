# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import pytz

_logger = logging.getLogger(__name__)



class MgsPayment(models.Model):
    _inherit = 'mgs.payment.transaction'
    _description = 'MGS Payment'
    _order = 'id desc'
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super(MgsPayment, self).create(vals_list)
        records = res.filtered(lambda x: x.method_code == 'tpluspay' and x.state not in ('cancel', 'duplicate'))
        records.filtered(lambda x: not x.partner_id).action_tpluspay_draft()
        records.filtered(lambda x: x.partner_id).action_tpluspay_confirm()
        return res

    def action_tpluspay_draft(self):
        payment_obj = self.env['account.payment']
        payment_method_line_id = self.env.ref(
            'mgs_tpluspay_integration.payment_method_tpluspay')

        mgs_unknown_partner_id_obj = self.env.company.mgs_unknown_partner_id
        if not payment_method_line_id:
            raise ValidationError(
                "No Payment method was found for this provider")

        if not mgs_unknown_partner_id_obj:
            raise ValidationError(
                "Please set a dummy partner to store all payments with unknown sources")
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

    def action_tpluspay_confirm(self):
        payment_obj = self.env['account.payment']
        payment_method_line_id = self.env.ref('mgs_tpluspay_integration.payment_method_tpluspay')
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


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(selection_add=[("tpluspay", "Tpluspay")], ondelete={"tpluspay": "set default"})
      
    tpluspay_user_id = fields.Char(string="Tpluspay User" )
    tpluspay_pass = fields.Char(string="Tpluspay Pass")
    
    
    auth_url = fields.Char(string="Auth Url" )
    sale_details = fields.Char(string="Sales Detail Url")
    trans_details = fields.Char(string="Transaction Url" )

    success_url = fields.Char(string="Success Url" )
    error_url = fields.Char(string="Error Url" )




class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res["tpluspay"] = {"mode": "unique", "domain": [("type", "=", "bank")]}
        return res






class TempPaymentData(models.Model):
    _name = "temp.payment.data"
    _description = "Temporary Payment Data Storage"
    

    partner_id = fields.Many2one("res.partner", string="Partner")
    date = fields.Datetime(
        string='date',
        default=fields.Datetime.now,
    )
    meter_no = fields.Char(string="Meter No.")
    amount = fields.Float("Amount")
    provider_id = fields.Many2one("payment.provider")
    code = fields.Char()
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending', string="Status")
