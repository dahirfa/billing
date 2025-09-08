# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_mgs_partner_prev_balance(self, partner_id=None, date=fields.Date.today()):
        params = [str(partner_id), 'asset_receivable', date]
        query = """
                SELECT COALESCE(sum(debit - credit), 0)
                FROM account_move_line aml
                LEFT JOIN account_account as aa ON aml.account_id=aa.id
                WHERE aml.partner_id = %s
                AND aa.account_type = %s
                AND aml.date < %s
                AND parent_state = 'posted' """
        self.env.cr.execute(query, tuple(params))
        data = self.env.cr.fetchone() or 0.0
        return data[0]


class MgsProperty(models.Model):
    _inherit = 'mgs_billing.property'

    # reference_name = fields.Char(string='Reference Name')
    # reference_mobile = fields.Char(string='Reference Mobile')
    technician = fields.Char(string='Technician')
    wires = fields.Char(string='Wires')
    poles = fields.Char(string='Poles')
    company_wires = fields.Char(string='Company Wires')
    company_poles = fields.Char(string='Company Poles')
    ref_name = fields.Char('Reference Name')
    ref_mobile = fields.Char('Reference Mobile')
    prop_type = fields.Selection(
        [('single', 'Single Phase'), ('three', 'Three Phase')], default="single", string='Type')
    customer_type = fields.Selection(
        [('normal', 'Normal Customer'), ('free', 'Free Customer'), ('shareholder', 'Shareholder')], string='Customer Type')
    security_deposit = fields.Float(string='Security Deposit')
    extra_charge_invoice_ids = fields.Many2many(
        'account.move', string='Invoices', ondelete='restrict', copy=False, readonly=True)

    note = fields.Char('Note')
    exclude_tax = fields.Boolean(string='Exclude Tax')

    def action_open_extra_charge_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Extra Charge Invoices',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.extra_charge_invoice_ids.ids)],
            'context': "{'create': False}"}


class MGSBillingReading(models.Model):
    _inherit = 'mgs_billing.reading'

    property_type_id = fields.Many2one(
        'mgs_billing.property.type', string='Property Type', related="property_id.property_type_id", store=True)
    customer_type = fields.Selection(
        [('normal', 'Normal Customer'), ('free', 'Free Customer'), ('shareholder', 'Shareholder')], related="property_id.customer_type", store=True)

    # def _prepare_invoice_line(self, service_ids):
    #     res = super(MGSBillingReading, self)._prepare_invoice_line(service_ids)
    #     if self.property_id.exclude_tax == True:
    #         for line in res:
    #             line['tax_ids'] = False
    #     return res

    def _prepare_invoice_line(self, service_ids):
        use_def = self.use_default_amount
        product_id = self.product_id
        difference = round(self.difference, 2)
        current_reading = round(self.current_reading, 2)
        last_reading = round(self.last_reading, 2)
        lines = []
        lines.append((0, 0, {
            'product_id': product_id.id if product_id else None,
            'name': "".join((product_id.name if product_id else None, " (", str(current_reading), ' - ', str(last_reading), ' = ', str(difference), ")")),
            'discount': self.discount,
            'quantity': difference if not use_def else 1,
            'price_unit': self.rate if not use_def else self.invoice_amount,
            'tax_ids': product_id.taxes_id.ids if not self.property_id.exclude_tax else False

        }))

        if len(service_ids.ids) > 0:
            for service in service_ids:
                lines.append((0, 0, {
                    'product_id': service.id if service.id else None,
                    'name': service.name,
                    'quantity': 1,
                    'price_unit': 1,
                }))
        return lines

    def action_confirm(self):
        meter_reading_obj = self.env['mgs_billing.meter.reading']
        for rec in self:
            if rec.property_id.customer_type == 'free':
                meter_reading_obj.create({'reading_id': rec.id})
                rec.state = 'posted'
            else:
                return super(MGSBillingReading, self).action_confirm()
