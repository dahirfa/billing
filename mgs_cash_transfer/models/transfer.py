from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CashTransfer(models.Model):
    _name = 'mgs_cash_transfer.transfer'
    _description = 'Cash Transfer'
    _inherit = ['mail.thread.main.attachment', 'mail.activity.mixin']

    name = fields.Char(string='Reference', copy=False, default='New')
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')
    memo = fields.Char(string='Memo')
    journal_id = fields.Many2one('account.journal', string='Source Journal (From)', required=True, domain=[('type', 'in', ['cash', 'bank'])])
    destination_journal_id = fields.Many2one('account.journal', string='Dest.Journal (To)', required=True, domain=[('type', 'in', ['cash', 'bank'])])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', copy=False)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', 'Currency', domain=[(
        'active', '=', True)], default=lambda self: self.env.company.currency_id.id, tracking=True)
    
    move_id = fields.Many2one('account.move', 'Journal Entry', index=True)

    def unlink(self):
        for record in self:
            if record.move_id and record.move_id.state == 'posted':
                raise UserError("You cannot delete a transfer with a posted move.")
        return super(CashTransfer, self).unlink()

    
    def _prepare_move_vals(self):
        """
        Prepare the values for creating an account move.
        """
        current_company = self.env.company
        transer_journal = current_company.mgs_transfer_journal_id
        if not transer_journal:
            raise UserError(_( "You can't create a new trasfer without an default transfer journal set on the company"))
        
        ref = 'Internal Transfer'

        if self.memo:
            ref += ": %s" % self.memo
        
        return [{
            'move_type': 'entry',
            'date': self.date,
            'journal_id': transer_journal.id,  
            'ref': ref,
            'name': '/'
        }]
    
    def _prepare_move_line_vals(self):
        current_company = self.env.company

        move_line_vals = [
            (0, 0, {
                'account_id': self.destination_journal_id.default_account_id.id,  # Bank/Cash account
                'partner_id': current_company.partner_id.id,
                'name': 'Transfer from %s' % self.journal_id.name,
                'debit': self.amount,
                'credit': 0.0,
                'date_maturity': self.date,
                'date': self.date,
                'currency_id': self.currency_id.id,
            }),
            (0, 0, {
                'account_id': self.journal_id.default_account_id.id,  # A/R account
                'partner_id': current_company.partner_id.id,
                'name': 'Transfer to %s' % self.destination_journal_id.name,
                'debit': 0.0,
                'credit': self.amount,
                'date_maturity': self.date,
                'date': self.date,
                'currency_id': self.currency_id.id,
            })
        ]

        return move_line_vals
    
    def action_post(self):
        for r in self:
            if r.move_id:
                # Override the existing move
                move_id = r.move_id
                move_vals = r._prepare_move_vals()[0]
                move_vals['line_ids'] = r._prepare_move_line_vals()
                r.move_id.line_ids.unlink()
                r.move_id.write(move_vals)
                r.move_id.action_post()
            else:
                # Create a new move
                move_vals = r._prepare_move_vals()[0]
                move_vals['line_ids'] = r._prepare_move_line_vals()
                move_id = self.env['account.move'].sudo().create(move_vals)
                move_id.action_post()
                r.move_id = move_id.id

            r.write({
                'state': 'posted',
                'name': move_id.name
            })
        return True


    def action_cancel(self):
        for r in self:
            r.write({
                'state': 'cancel',
            })
            r.move_id.button_cancel()

    def action_reset_to_draft(self):
        for r in self:
            r.write({
                'state': 'draft',
            })
            r.move_id.button_draft()

    def button_open_journal_entry(self):
        action = self.env.ref('account.action_move_journal_line').sudo().read()[0]
        action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        action['res_id'] = self.move_id.id
        return action