from odoo import models, fields, api, tools
from datetime import datetime, date
from odoo.exceptions import UserError, AccessError


class ApplyExtraChargetWiz(models.TransientModel):
    _name = 'mgs_billing.apply_extra_charge.wizard'
    _description = 'Apply Extra Charge Wizard'

    # operation_type = fields.Selection([('suspension', 'Duspension'), ('suspension', 'Duspension')], string='Month',
    #                          required=True, default=str(date.today().month))
    apply_charge = fields.Boolean(default=False, string='Apply Charge')
    product_id = fields.Many2one(
        'product.product', index=True, string="Charge Type")
    property_id = fields.Many2one(
        'mgs_billing.property', index=True, string="Property")
    partner_id = fields.Many2one(
        'res.partner', index=True, string="Customer")
    memo = fields.Text(string='Memo')
    amount = fields.Float(string='Amount', default=1)

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    invoice_id = fields.Many2one(
        'account.move', index=True, string="Invoice")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product_id = self.product_id
        if product_id:
            self.amount = product_id.list_price
            self.memo = product_id.name

    @api.model
    def default_get(self, fields):
        rec = super(ApplyExtraChargetWiz, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        property_id = self.env[active_model].browse(active_ids)
        partner_obj = self.env['res.partner']
        domain = [('is_tenancy', '=', True),
                  ('property_id', '=', property_id.id)]
        partner_id = partner_obj.search(domain, limit=1)

        rec.update({
            'partner_id': partner_id.id,
            'property_id': property_id.id,
        })
        return rec

    def _prepare_invoice_data(self):
        company = self.env.company or self.company_id
        product_id = self.product_id
        zone_journal = self.property_id.zone_id.journal_id or self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)

        # default_journal = self.env['account.move'].with_context(
        #     default_move_type='out_invoice')._get_default_journal()

        journal = zone_journal

        if not journal:
            raise UserError(
                'Please define a sale journal for the company "%s".') % company.name or ''

        if not self.partner_id:
            raise UserError(
                "There's no customer associated with this property!.")

        partner_id = self.partner_id
        res = {
            'move_type': 'out_invoice',
            'partner_id': partner_id.id,
            'currency_id': company.currency_id.id,
            'journal_id': journal.id,
            'invoice_origin': 'Extra Charge',
            'partner_bank_id': company.partner_id.bank_ids.filtered(lambda b: not b.company_id or b.company_id == company)[:1].id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product_id.id if product_id else None,
                'name': product_id.name,
                'quantity': 1,
                'price_unit': self.amount
            })]
        }
        return res

    def create_invoice(self):
        """
        Create the invoice associated to the appointment.
        :param grouped: if True, invoices are grouped by TO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        for rec in self:
            if rec.invoice_id:
                return True

            invoice_vals = rec._prepare_invoice_data()

            move = self.env['account.move'].sudo().with_context(
                default_move_type='out_invoice').create(invoice_vals)
            move.action_post()
            rec.invoice_id = move

            return True

            # action = self.env.ref(
            #     'account.action_move_out_invoice_type').read()[0]
            # action['views'] = [
            #     (self.env.ref('account.view_move_form').id, 'form')]
            # action['res_id'] = move.id
            # return action

    # def action_open_invoice(self):
    #     action = self.env.ref(
    #         'account.action_move_out_invoice_type').sudo().read()[0]
    #     action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
    #     action['res_id'] = self.invoice_id.id
    #     return action

    def action_confirm(self):
        if self.apply_charge == True:
            self.create_invoice()

        self.property_id.suspended = True
        self.property_id.extra_charge_invoice_ids = [(4, self.invoice_id.id)]
