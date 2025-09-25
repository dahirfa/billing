# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import pytz

class MgsPaymentBaseJournal(models.Model):
    _inherit = 'account.journal'
    _rec_names_search = ['name', 'code', 'mgs_bank_no']

    mgs_bank_no = fields.Char()


class MgsPaymentBase(models.Model):
    _name = 'mgs.payment.base'
    _description = 'Mgs payment Base'

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)
    move_id = fields.Many2one('account.move')
    breakdown = fields.Boolean(default=False)

    def get_partner_balance(self, id):
        partner_balance = """
                            select COALESCE(sum(aml.debit - aml.credit), 0)
                            from account_move_line as aml
                            left join account_account as aa on aml.account_id=aa.id
                            where aml.partner_id = %s""" % str(id) + """
                            and aa.account_type = 'asset_receivable'
                            and parent_state in ('posted')"""
        self.env.cr.execute(partner_balance)
        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result


class PaymentInherit(models.Model):
    _inherit = 'account.payment'

    mgs_sender_phone = fields.Char(string='Sender Phone')
    mgs_transaction_ref = fields.Char(string='Transaction Ref')
    mgs_p_transaction_id = fields.Many2one('mgs.payment.transaction')
    mgs_payment_line_id = fields.Many2one('mgs.payment.line')
    mgs_partner_bal = fields.Monetary(
        string='Balance', compute="_compute_mgs_partner_bal", store=True)
    
    
    zone_id = fields.Many2one(
        string='Zone',
        related='partner_id.zone_id',
        comodel_name='mgs_billing.zone',
        ondelete='restrict',
    )
    

    @api.depends('partner_id')
    def _compute_mgs_partner_bal(self):
        for r in self:
            r.mgs_partner_bal = 0.0
            if r.partner_id:
                params = [str(r.partner_id.id), 'asset_receivable']
                query = """
                        SELECT COALESCE (sum(debit - credit), 0)
                        FROM account_move_line aml
                        LEFT JOIN account_account as aa ON aml.account_id=aa.id
                        WHERE aml.partner_id = %s
                        AND aa.account_type = %s
                        AND parent_state = 'posted' """
                self.env.cr.execute(query, tuple(params))
                data                = self.env.cr.fetchone()
                r.mgs_partner_bal   = data[0]



    def unlink(self):
        for r in self:
            if r.state == 'posted':
                raise UserError("You can't unlink posted payments")
        return super(PaymentInherit, self).unlink()

    def action_draft(self):
        for r in self:
            if self.env.user.has_group('base.group_system'):
                return super(PaymentInherit, self).action_draft()
            if r.mgs_p_transaction_id and 'allow_action' not in self.env.context:
                raise UserError("Action not allowed!")
        return super(PaymentInherit, self).action_draft()

    def action_cancel(self):
        for r in self:
            if self.env.user.has_group('base.group_system'):
                return super(PaymentInherit, self).action_cancel()
            if r.mgs_p_transaction_id and 'allow_action' not in self.env.context:
                raise UserError("Action not allowed!")
        return super(PaymentInherit, self).action_cancel()

    def action_post(self):
        res = super(PaymentInherit, self).action_post()
        for r in self:
            r.partner_id.alternative_number = r.mgs_sender_phone
            if self.env.user.has_group('base.group_system'):
                r.mgs_action_reconcile()
                return res
            if r.mgs_p_transaction_id and 'allow_action' not in self.env.context:
                raise UserError("Action not allowed!")
            if self._allow_reconcile():
                r.mgs_action_reconcile()
        return res
    
    
    
    def _allow_reconcile(self):
        for rec in self:
            return True

    def mgs_get_receivables(self, partner_id, move_line_obj):
        move_lines = move_line_obj.search([('move_id.state', '=', 'posted'), ('partner_id.id', '=', partner_id), (
            'account_id.account_type', '=', 'asset_receivable'), ('reconciled', '=', False)], order='date DESC').mapped('id')
        return move_lines

    def mgs_action_reconcile(self):
        # move_line_obj=self.env['account.move.line']
        for rec in self.filtered(lambda x: x.partner_id):
            lines = rec.move_id.line_ids
            payment_line = lines.filtered(
                lambda x: x.account_id.account_type == 'asset_receivable')
            if payment_line:
                reconcile_with = self.mgs_get_receivables(
                    rec.partner_id.id, lines)
                m_list = [payment_line.id]
                m_list.extend(reconcile_with)
                moves = lines.browse(m_list)
                if moves:
                    moves.reconcile()

    
    def action_open_mgs_payment(self):
        self.ensure_one()        
        if self.mgs_p_transaction_id:
            action = self.env.ref(
                'mgs_payment_integration.action_mgs_e_payment_transaction').sudo().read()[0]
            action['views'] = [
                (self.env.ref('mgs_payment_integration.mgs_payment_transaction_form').id, 'form')]
            action['res_id'] = self.mgs_p_transaction_id.id
            action['context'] = {'create': False}
            return action

    
        
        
    

class PaymentLine(models.Model):
    _name = 'mgs.payment.line'
    _description = "Payment line"

    name = fields.Char()
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    amount = fields.Monetary(string='Amount')
    payment_id = fields.Many2one('account.payment', string='Payment')
    partner_id = fields.Many2one(
        'res.partner', string='Billing Account', required=True)
    transaction_id = fields.Many2one(
        'mgs.payment.transaction', string='Transaction')

    def _prepare_payment(self, journal_id, ref, sender, date):
        return {
            'mgs_payment_line_id': self.id,
            'partner_id':           self.partner_id.id,
            'amount':               self.amount,
            'date':                 date,
            'mgs_transaction_ref':  ref,
            'mgs_sender_phone':     sender if sender else None,
            'journal_id':           journal_id,
            'payment_type':         'inbound',
        }


class Payment(models.Model):
    _name = 'mgs.payment.transaction'
    _description = 'Customer Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'mgs.payment.base']

    name = fields.Char(string='Ref', tracking=True)

    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    amount = fields.Monetary(string='Amount', tracking=True)
    description = fields.Char(string='Description', tracking=True)
    date = fields.Datetime(string='Date', tracking=True)
    payment_id = fields.Many2one(
        'account.payment', string='Payment', tracking=True)
    payment_ids = fields.One2many(
        'account.payment', 'mgs_p_transaction_id', string='Payments', tracking=True)
    line_ids = fields.One2many(
        'mgs.payment.line', 'transaction_id', tracking=True)
    invoice_ids = fields.Many2one(
        'account.move', string='Invoices', tracking=True)
    partner_id = fields.Many2one(
        'res.partner', string='Partner', tracking=True)
    content = fields.Char(string='Content', tracking=True)
    method_id = fields.Many2one(
        'payment.provider', string='Payment Method', tracking=True)
    state = fields.Selection([('draft', 'New'), ('duplicate', 'Duplicate'), ('pending', 'Pending'), (
        'confirm', 'Confirmed'), ('cancel', 'Canceled')], default='draft', tracking=True)
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[
                                 ('type', '=', 'bank')], tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    ref = fields.Char(string='Ref', tracking=True)
    method_code = fields.Selection(
        related='method_id.code', store=True, tracking=True)
    paid_by = fields.Char(tracking=True)
     
    def _prepare_payment_vals(self, payment_method_line_id, partner_id):
        journal_id = self.journal_id
        method_line_id = journal_id.inbound_payment_method_line_ids.filtered(
            lambda x: x.payment_method_id.id == payment_method_line_id)
        target_timezone = pytz.timezone('Africa/Mogadishu')
        date = self.date.astimezone(target_timezone)
        return {
            'mgs_p_transaction_id':     self.id,
            'partner_id':               partner_id.id,
            'amount':                   self.amount,
            'date':                     date,
            'journal_id':               journal_id.id,
            'payment_method_line_id':   method_line_id.id,
            'mgs_transaction_ref':      self.name,
            'mgs_sender_phone':         self.paid_by if self.paid_by else None,
            'payment_type':             'inbound',
        }
    
    
    
    @api.model_create_multi
    def create(self, vals_list):
        # mpt = self.env['mgs.golis.sahal.payment']
        ap = self.env['account.payment']

        for vals in vals_list:
            transactionid = vals.get('name')
            journal_clause = ('journal_id.id', '=', vals.get('journal_id'))
            # TODO: TRANSFER TO SAHAL IMPORT
            # if self.search_count([('name', '=', transactionid), journal_clause]) or mpt.search_count([('transactionid', '=', transactionid), journal_clause]) or ap.search_count([('mgs_transaction_ref', '=', transactionid), journal_clause]):
            if self.search_count([('name', '=', transactionid), journal_clause]) or ap.search_count([('mgs_transaction_ref', '=', transactionid), journal_clause]):
                vals['state'] = 'duplicate'
                vals['active'] = False
            else:
                vals['state'] = 'pending'
        return super(Payment, self).create(vals_list)

    @api.onchange('breakdown')
    def onchange_breakdown(self):
        if self.state != 'confirm':
            self.partner_id = None
            self.line_ids = None

    def unlink(self):
        with_payment = self.filtered(lambda x: x.payment_id)
        if with_payment:
            raise ValidationError('You cannot unlink this record')
        res = super(Payment, self).unlink()
        return res

    def _set_draft(self):
        self.write({'state': 'draft'})

    def _set_pending(self):
        self.write({'state': 'pending'})

    def _set_confirm(self):
        self.write({'state': 'confirm'})

    def _set_cancel(self):
        self.write({'state': 'cancel'})

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
