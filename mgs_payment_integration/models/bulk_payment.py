from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    bulk_payment_id = fields.Many2one('mgs_payment_integration.bulk_payment', string='Bulk Payment')
    zone_id = fields.Many2one('mgs_billing.zone', string='Zone', related="partner_id.property_id.zone_id", store=True)

    def action_draft(self):
        for r in self:
            if self.env.user.has_group('base.group_system'):
                return super(AccountPayment, self).action_draft()
            if r.bulk_payment_id and 'allow_action' not in self.env.context:
                raise UserError("Action not allowed!")
        return super(AccountPayment, self).action_draft()

    def action_cancel(self):
        for r in self:
            if self.env.user.has_group('base.group_system'):
                return super(AccountPayment, self).action_cancel()
            if r.bulk_payment_id and 'allow_action' not in self.env.context:
                raise UserError("Action not allowed!")
        return super(AccountPayment, self).action_cancel()


    def action_post(self):
        for r in self:
            if self.env.user.has_group('base.group_system'):
                return super(AccountPayment, self).action_post()
            
            if r.bulk_payment_id and 'allow_action' not in self.env.context:
                raise UserError("Action not allowed!")
        res = super(AccountPayment, self).action_post()
        return res

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        res = super(AccountPayment, self)._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals, force_balance=None)
        mgs_sender_phone = self.mgs_sender_phone
        if self.payment_type == 'inbound' and self.partner_id.id:
            res[1]['name'] += '| by: %s' % mgs_sender_phone if mgs_sender_phone else ''
        return res

    def action_open_bulk_payment(self):
        self.ensure_one()
        if self.bulk_payment_id:
            action = self.env.ref('mgs_payment_integration.action_bulk_payment').sudo().read()[0]
            action['views'] = [(self.env.ref('mgs_payment_integration.view_bulk_payment_form').id, 'form')]
            action['res_id'] = self.bulk_payment_id.id
            action['context'] = {'create': False}
            return action

        
     


class BulkPayment(models.Model):
    _name = 'mgs_payment_integration.bulk_payment'
    _description = 'Bulk Payment'
    _order = 'id desc'

    name = fields.Char(string='Bulk Payment #')
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[
                                 ('type', 'in', ['cash', 'bank'])])
    date = fields.Date(string='Date', default=lambda self: fields.Date.today())
    payment_lines = fields.One2many(
        'mgs_payment_integration.bulk_payment_line', 'bulk_payment_id', string='Payment Lines')
    amount = fields.Float(string='Amount')
    total = fields.Float(string='Total', compute='_compute_total', store=True)
    state = fields.Selection(
        [('draft', 'To Confirm'), ('confirm', 'Confirmed'), ('cancel', 'Cancel')], default='draft', tracking=True)
    payment_count = fields.Integer(
        compute='_count_paments', string="Payment", tracking=True)
    payment_ids = fields.One2many(
        'account.payment', 'bulk_payment_id', tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id, tracking=True)
    mgs_sender_phone = fields.Char(string='Sender Phone')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = vals['name'] = self.env['ir.sequence'].next_by_code(
                'mgs_payment_integration.bulk_payment') or '/'
        res = super(BulkPayment, self).create(vals_list)
        return res

    @api.depends('payment_ids')
    def _count_paments(self):
        for r in self:
            r.payment_count = len(r.payment_ids)

    @api.depends('payment_lines.amount')
    def _compute_total(self):
        for payment in self:
            payment.total = sum(payment.payment_lines.mapped('amount'))

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

    def action_confirm(self):
        payment_obj = self.env['account.payment']
        for payment in self:
            journal_id = payment.journal_id

            if payment.state == 'confirm':
                raise ValidationError("This record is already confirmed")

            break_down_total = payment.total
            amount = payment.amount

            if round(break_down_total, 2) != round(amount, 2):
                raise ValidationError(
                    "Amount must be equal to the total amount")
            for line in payment.payment_lines.filtered(lambda p: p.payment_id.state != 'posted'):
                new_payment = line.payment_id
                if line.payment_id:
                    new_payment.update({
                        'bulk_payment_id':      payment.id,
                        'partner_id':           line.partner_id,
                        'amount':               line.amount,
                        'date':                 line.bulk_payment_id.date,
                        'journal_id':           journal_id,
                        'payment_type':         'inbound',
                        'mgs_sender_phone':      payment.mgs_sender_phone
                    })
                else:
                    vals = line._prepare_payment_vals(journal_id.id)
                    new_payment = payment_obj.create(vals)
                    line.payment_id = new_payment.id
                self.env.cr.commit()
                new_payment.with_context(allow_action=True).action_post()

            payment.state = 'confirm'

    def unlink(self):
        with_payment = self.payment_ids.filtered(lambda x: x.state == 'posted')
        if len(with_payment) > 0:
            raise ValidationError('You cannot unlink this record')
        res = super(BulkPayment, self).unlink()
        return res

    def action_draft(self):
        for payment in self:
            for line in payment.payment_lines:
                if line.payment_id:
                    line.payment_id.with_context(
                        allow_action=True).action_draft()

            payment.state = 'draft'

    def action_cancel(self):
        for payment in self:
            for line in payment.payment_lines:
                if line.payment_id:
                    line.payment_id.with_context(
                        allow_action=True).action_cancel()

            payment.state = 'cancel'


class BulkPaymentLine(models.Model):
    _name = 'mgs_payment_integration.bulk_payment_line'
    _description = 'Bulk Payment Line'

    bulk_payment_id = fields.Many2one(
        'mgs_payment_integration.bulk_payment', string='Bulk Payment')
    partner_id = fields.Many2one('res.partner', string='Partner')
    payment_id = fields.Many2one('account.payment', string='Payment')
    amount = fields.Float(string='Amount')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id, tracking=True)

    def _prepare_payment_vals(self, journal_id):
        return {
            'bulk_payment_id':      self.bulk_payment_id.id,
            'partner_id':           self.partner_id.id,
            'amount':               self.amount,
            'date':                 self.bulk_payment_id.date,
            'journal_id':           journal_id,
            'payment_type':         'inbound',
            'memo':                  self.bulk_payment_id.name,
            'mgs_sender_phone':     self.bulk_payment_id.mgs_sender_phone,
            'company_id':           self.company_id.id
        }
