from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class BalanceTransfer(models.Model):
    _name = 'mgs_necsom_addons.balance_transfer'
    _description = 'Balance Transfer'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Transfer #')

    date = fields.Date(string='Date', default=lambda self: fields.Date.today())
    billing_account_id = fields.Many2one('res.partner', compute='_get_tenant', string='Billing Account', index=True, domain=[
                                         ('is_tenancy', '=', True)], store=True, tracking=True)
    cust_balance = fields.Float(
        string='Balance', default=0.0, compute='_compute_cust_balance', store=True)

    transfer_lines = fields.One2many(
        'mgs_necsom_addons.balance_transfer_line', 'transfer_id', string='Transfer Lines')

    state = fields.Selection(
        [('draft', 'To Confirm'), ('confirm', 'Confirmed'), ('cancel', 'Cancel')], default='draft', tracking=True)

    move_id = fields.Many2one(
        'account.move', tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id, tracking=True)
    total = fields.Float(string='Total', compute='_compute_total', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = vals['name'] = self.env['ir.sequence'].next_by_code(
                'mgs_necsom_addons.balance_transfer') or '/'
        res = super(BalanceTransfer, self).create(vals_list)
        return res

    @api.depends('billing_account_id')
    def _compute_cust_balance(self):
        for r in self:
            r.cust_balance = r.billing_account_id.mgs_credit or 0.0

    @api.depends('transfer_lines.amount')
    def _compute_total(self):
        for trasfer in self:
            trasfer.total = sum(trasfer.transfer_lines.mapped('amount'))

    def action_open_journal_entry(self):
        action = self.env.ref(
            'account.action_move_journal_line').sudo().read()[0]
        action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        action['res_id'] = self.move_id.id
        return action

    def _prepare_move_values(self):
        journal_id = self.env['account.journal'].search(
            [('type', '=', 'general')], order="sequence asc", limit=1)
        # self.ensure_one()
        move_values = {}
        for r in self:
            move_values = {
                'journal_id': journal_id.id,
                'company_id': r.company_id.id,
                'date': r.date,
                'ref': 'Balance Transfer',
                'currency_id': r.company_id.currency_id.id,
                # force the name to the default value, to avoid an eventual 'default_name' in the context
                # to set it to '' which cause no number to be given to the account.move when posted.
                'name': '/',
            }
        return move_values

    def _prepare_move_line_values(self, transfer_lines):
        move_line_values = []
        for line in transfer_lines:

            account_date = line.transfer_id.date
            partner_id_src = line.partner_id
            partner_id_dst = line.transfer_id.billing_account_id
            account_src = partner_id_src.property_account_receivable_id.id
            account_dst = partner_id_dst.property_account_receivable_id.id
            company_id = line.transfer_id.company_id
            currency_id = company_id.currency_id.id
            balance = line.amount
            name = line.transfer_id.name

            # first line
            move_line_src = {
                'name': 'Balance transfer from %s' % partner_id_dst.property_id.name,
                'debit': balance,
                'credit': 0,
                'partner_id': partner_id_src.id,
                'account_id': account_src,
                'date_maturity': account_date,
                'currency_id': currency_id,
            }

            move_line_values.append((0, 0, move_line_src))

            # second move line
            move_line_dst = {
                'name': 'Balance transfer to %s' % partner_id_src.property_id.name,
                'quantity': 1,
                'debit': 0,
                'credit': balance,
                'account_id': account_dst,
                'partner_id': partner_id_dst.id,
                'currency_id': currency_id,
            }
            move_line_values.append((0, 0, move_line_dst))

        return move_line_values

    def action_confirm(self):
        for transfer in self:

            if transfer.state == 'confirm':
                raise ValidationError("This record is already confirmed")

            break_down_total = transfer.total
            amount = transfer.cust_balance

            if round(break_down_total, 2) > round(amount, 2):
                raise ValidationError(
                    "Amount must be equal to the total amount")

            move_line_vals = transfer._prepare_move_line_values(
                transfer.transfer_lines)
            move = transfer.move_id
            if move:
                move.line_ids = None
                move.line_ids = move_line_vals
            else:
                move_vals = transfer._prepare_move_values()
                move = self.env['account.move'].with_context(
                    default_journal_id=move_vals['journal_id']).create(move_vals)
                move['line_ids'] = move_line_vals

            move.action_post()

            transfer.move_id = move
            transfer.state = 'confirm'

    def unlink(self):
        if self.move_id and self.move_id == 'posted':
            raise ValidationError('You cannot unlink this record')
        res = super(BalanceTransfer, self).unlink()
        return res

    def action_draft(self):
        self.move_id.button_draft()
        self.state = 'draft'

    def action_cancel(self):
        self.move_id.button_cancel()
        self.state = 'cancel'


class BalanceTransferLine(models.Model):
    _name = 'mgs_necsom_addons.balance_transfer_line'
    _description = 'Balance Transfer Line'

    transfer_id = fields.Many2one(
        'mgs_necsom_addons.balance_transfer', string='Balance Transfer')
    partner_id = fields.Many2one('res.partner', string='Partner')
    amount = fields.Float(string='Amount')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id, tracking=True)
