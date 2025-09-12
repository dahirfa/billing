from odoo import models, fields, api, _
import calendar
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils


class MGSBillingMeterReadings(models.Model):
    _name = 'mgs_billing.meter.reading'
    _description = 'Billing Meter Reading'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reading_id'
    # name  = fields.Char()

    reading_id = fields.Many2one(
        'mgs_billing.reading', string='Reading #', ondelete="restrict")  # , required=True
    date = fields.Date(string='Date', compute='_get_reading_info', store=True)
    property_id = fields.Many2one(
        'mgs_billing.property', string='Property', compute='_get_reading_info', store=True)
    billing_account_id = fields.Many2one(
        'res.partner', string='Billing Account', compute='_get_reading_info', store=True)
    product_id = fields.Many2one(
        'product.product', string='plan', compute='_get_reading_info', store=True)
    move_id = fields.Many2one(
        'account.move', string='Invoice', compute='_get_reading_info', store=True)
    uom_id = fields.Many2one('uom.uom', string='Uom',
                             compute='_get_reading_info', store=True)
    reading_on_date = fields.Float(compute='_get_reading_info', store=True)
    previous_reading = fields.Float(compute='_get_reading_info', store=True)
    reading_difference = fields.Float(compute='_get_reading_info', store=True)
    rate = fields.Float(compute='_get_reading_info', store=True)
    currency_id = fields.Many2one(
        'res.currency', 'Currency', compute='_get_reading_info', store=True)
    invoice_amount = fields.Monetary(compute='_get_reading_info', store=True)
    state = fields.Selection(related='reading_id.state', store=True)
    zone_id = fields.Many2one(
        'mgs_billing.zone', related='property_id.zone_id', store=True)
    comment = fields.Char(string="Comment")

    @api.depends('reading_id')
    def _get_reading_info(self):
        for r in self:
            r.product_id = r.reading_id.product_id.id
            r.billing_account_id = r.reading_id.billing_account_id.id
            r.date = r.reading_id.date
            r.property_id = r.reading_id.property_id.id
            r.uom_id = r.reading_id.uom_id.id
            r.move_id = r.reading_id.move_id.id
            r.currency_id = r.move_id.currency_id.id
            r.reading_on_date = r.reading_id.current_reading
            r.previous_reading = r.reading_id.last_reading
            r.reading_difference = r.reading_id.difference
            r.rate = r.reading_id.rate
            r.invoice_amount = r.reading_id.amount_total

    def unlink(self):
        raise UserError("You cannot delete reading history.")
        return super(MGSBillingMeterReadings, self).unlink()

class MGSBillingReading(models.Model):
    _name = 'mgs_billing.reading'
    _description = 'Billing Reading'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id DESC"
    
    @api.onchange('property_id')
    def onchange_property_id(self):
        if self.property_id:
            self.current_reading =  self.last_reading
    
    name = fields.Char(string='Reading #', default='/', index=True)
    date = fields.Date(string='Date', default=fields.Date.today(), index=True)
    inv_date = fields.Date(related="move_id.invoice_date", store=True)
    current_reading = fields.Float(string="Current Reading", tracking=True)
    last_reading = fields.Float(
        string="Last Reading", compute='_get_last_reading', store=True)
    difference = fields.Float(
        string='Difference', default=0.0, compute='_compute_difference', store=True)
    property_id = fields.Many2one(
        'mgs_billing.property', index=True, string='Property', required=True, tracking=True)
    billing_account_id = fields.Many2one('res.partner', compute='_get_tenant', string='Billing Account', index=True, domain=[
                                         ('is_tenancy', '=', True)], store=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id, tracking=True)
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True, default=lambda self: self.env.company.currency_id.id, tracking=True)
    uom_id = fields.Many2one(
        'uom.uom', compute='_compute_uom', string='Unit of Measure', store=True)
    discount = fields.Float(string='Discount (%)',
                            digits='Discount', readonly=False, store=True, tracking=True)
    rate = fields.Monetary(
        string='Price/Unit', compute="_get_pricelist_price", readonly=False, store=True, copy=False, tracking=True)
    comment = fields.Char(string='Comment', tracking=True)

    use_default_amount = fields.Boolean(
        string='Default amount', compute='_compute_def_amount', store=True)
    amount_total = fields.Monetary(
        string='Total', compute='_compute_total_amount', store=True, tracking=True)
    invoice_amount = fields.Monetary(
        string='Invoice Amount', compute='_compute_total_amount', store=True, tracking=True)

    move_id = fields.Many2one(
        'account.move', string='Invoice', copy=False, index=True, tracking=True)
    counter = fields.Integer(string='Invoice', compute='_compute_counter')
    product_id = fields.Many2one(
        'product.product', string='Plan', compute='_get_product', store=True)
    meter_reading_id = fields.Many2one(
        'mgs_billing.meter.reading', string='Reading',)
    zone_id = fields.Many2one(
        'mgs_billing.zone', related='property_id.zone_id', store=True, tracking=True)
    collector_id = fields.Many2one(
        'res.partner', domain=[('is_collector', '=', True)], related='zone_id.collector_id', store=True)
    state = fields.Selection(
        [('draft', 'draft'), ('pending', 'Pending'), ('posted', 'Posted'), ('cancel', 'Cancelled')], default='draft', tracking=True, index=True)
    payment_state = fields.Selection(
        related='move_id.payment_state', store=True, tracking=True)
    warning_message = fields.Char(
        string='Warning Message', compute='_check_usage', store=True)
    unusual_usage = fields.Boolean(
        string='unusual Usage', compute='_check_usage', store=True, tracking=True)

    average_usage = fields.Float(compute="_get_tenant", string="Normal Usage")
    pricelist_id = fields.Many2one(
        'product.pricelist',
        string="Pricelist",
        compute='_compute_pricelist_id',
        store=True, readonly=False, check_company=True,
        tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    invoiced_amount = fields.Monetary(related='move_id.amount_total')
    allow_extra_reading = fields.Boolean(default=False)

    billed_before = fields.Boolean(
        default=False, compute="_compute_billed_before", store=True, copy=False)

    @api.constrains('property_id', 'billed_before')
    def check_property_billed(self):
        for r in self:
            if not r.allow_extra_reading and r.billed_before:
                raise ValidationError('This Property is already billed.')

    @api.constrains('current_reading', 'last_reading')
    def check_current_reading(self):
        for r in self:
            if r.current_reading < r.last_reading:
                raise ValidationError(
                    'current reading must be greater than the last reading')

    def _get_billed_unbilled(self, date, property_id):
        start = self.env.company.billing_period_start
        end = self.env.company.billing_period_end
        result = False
        st, en = date_utils.get_billing_start_and_end_dates(date, start, end)
        if self.search_count([('state', '=', 'posted'), ('property_id.id', '=', property_id), ('date', '>=', st), ('date', '<=', en)]) > 0:
            result = True
        return result

    @api.depends('date', 'property_id')
    def _compute_billed_before(self):
        for r in self:
            r.billed_before = self._get_billed_unbilled(
                r.date, r.property_id.id)

    @api.depends('billing_account_id')
    def _compute_pricelist_id(self):
        for reading in self:
            if not reading.billing_account_id:
                reading.pricelist_id = False
                continue
            reading = reading.with_company(reading.company_id)
            reading.pricelist_id = reading.billing_account_id.property_product_pricelist.id

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'mgs_billing.reading') or '/'
        return super(MGSBillingReading, self).create(vals_list)

    def unlink(self):
        if self.move_id:
            raise UserError(
                "You cannot delete reading which has related invoice.")
        return super(MGSBillingReading, self).unlink()

    def action_cancel(self):
        for r in self:
            if r.move_id:
                r.move_id.with_context(allow_action=True).button_draft()
                r.move_id.with_context(allow_action=True).button_cancel()
            r.write({'state': 'cancel'})

    def action_confirm(self):
        move_obj = self.env['account.move']
        meter_reading_obj = self.env['mgs_billing.meter.reading']
        start = self.env.company.billing_period_start
        end = self.env.company.billing_period_end
        service_ids = self.env.company.mgs_extra_service_ids

        for rec in self:
            start_date, end_date = date_utils.get_billing_start_and_end_dates(
                rec.date, start, end)
            move_id = rec.move_id
            if not move_id:
                post_meter_reading = meter_reading_obj.create({'reading_id': rec.id})
                if post_meter_reading:
                    rec.meter_reading_id = post_meter_reading.id
                    prepared_invoice = rec._prepare_invoice(
                        start_date, end_date, service_ids)
                    creatd_move = move_obj.create(prepared_invoice)
                    creatd_move.with_context(allow_action=True).action_post()
                    rec.write({'move_id': creatd_move.id})
                else:
                    raise ValidationError("Could not post the meter reading")
            if move_id:
                move_id.write(rec._prepare_invoice_data(start_date, end_date))
                rec.meter_reading_id.write({'reading_id': rec.id})
                move_id.invoice_line_ids = None
                move_id.invoice_line_ids = rec._prepare_invoice_line(
                    service_ids)
                move_id.with_context(allow_action=True).action_post()
            rec.write({'state': 'posted'})

    def action_draft(self):
        for r in self:
            if r.move_id:
                r.move_id.with_context(allow_action=True).button_draft()
            r.write({'state': 'draft'})

    def action_pend(self):
        self.write({'state': 'pending'})

    def _prepare_invoice_line(self, service_ids):
        use_def = self.use_default_amount
        product_id = self.product_id
        difference = round(self.difference, 2)
        current_reading = round(self.current_reading, 2)
        last_reading = round(self.last_reading, 2)
        lines = []
        lines.append((0, 0, {
            'product_id': product_id.id if product_id else None,
            'name': "".join((product_id.name if product_id else None, "= (", str(current_reading), ' - ', str(last_reading), ' = ', str(difference), ")")),
            'discount': self.discount,
            'quantity': difference if not use_def else 1,
            'price_unit': self.rate if not use_def else self.invoice_amount,

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

    def _prepare_invoice_data(self, start_date, end_date):
        company = self.env.company or self.company_id
        journal = self.property_id.zone_id.journal_id or self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
        if not journal:
            raise UserError(_('Please define a sale journal for the company "%s".') % (
                company.name or '', ))
        partner_id = self.billing_account_id.id
        last_day = calendar.monthrange(start_date.year, start_date.month)[1]
        last_day_date = start_date.replace(day=last_day)
        new_month_date = end_date.replace(day=1)
        invoice_date = self.date if self.date < new_month_date else start_date.replace(day=last_day)
        res = {
            'move_type': 'out_invoice',
            'invoice_date': invoice_date,
            'partner_id': partner_id,
            'currency_id': self.currency_id.id,
            'journal_id': journal.id,
            'invoice_origin': self.name + " (" + str(self.current_reading) + ' - ' + str(self.last_reading) + ' = ' + str(self.difference) + ")",
            'partner_bank_id': company.partner_id.bank_ids.filtered(lambda b: not b.company_id or b.company_id == company)[:1].id,
            'reading_id': self.id}
        return res

    def _prepare_invoice(self, start_date, end_date, service_ids):
        invoice = self._prepare_invoice_data(start_date, end_date)
        invoice['invoice_line_ids'] = self._prepare_invoice_line(service_ids)
        return invoice

    @api.depends('move_id')
    def _compute_counter(self):
        for r in self:
            r.counter = len(r.move_id)

    def action_open_invoice(self):
        action = self.env.ref(
            'account.action_move_out_invoice_type').sudo().read()[0]
        action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        action['res_id'] = self.move_id.id
        return action

    @api.depends('billing_account_id', 'difference')
    def _check_usage(self):
        max_above_avg = self.env.company.max_above_avg
        max_under_avg = self.env.company.max_under_avg

        for rec in self:
            if rec.last_reading and rec.average_usage > 0.0:
                diff = rec.difference
                avg = rec.average_usage
                if diff >= (max_above_avg*avg) or diff <= (max_under_avg*avg):
                    rec.warning_message = "warning : Unusual usage"
                    rec.unusual_usage = True
                else:
                    rec.warning_message = ""
                    rec.unusual_usage = False
            else:
                rec.warning_message = ""
                rec.unusual_usage = False


    @api.depends('difference')
    def _compute_def_amount(self):
        mgs_billing_if_its_less_than = self.env.company.mgs_billing_if_its_less_than
        for r in self:
            r.use_default_amount = True if r.difference < mgs_billing_if_its_less_than else False

    @api.depends('rate', 'difference', 'discount', 'use_default_amount')
    def _compute_total_amount(self):
        mgs_billing_default_amount = self.env.company.mgs_billing_make_rate
        for r in self:
            difference = r.difference
            price = r.rate * (1 - (r.discount or 0.0) / 100.0)
            r.amount_total = price * difference
            r.invoice_amount = r.amount_total if not r.use_default_amount else mgs_billing_default_amount

    @api.depends('billing_account_id')
    def _get_product(self):
        for r in self:
            r.product_id = r.billing_account_id.product_id.id


    @api.depends('billing_account_id', 'pricelist_id', 'product_id', 'difference')
    def _get_pricelist_price(self):
        for r in self:
            pricelist_id = r.pricelist_id
            if r.product_id:
                r.rate = pricelist_id._price_get(r.product_id, r.difference)[
                    pricelist_id.id]

    @api.depends('billing_account_id')
    def _compute_uom(self):
        for r in self:
            product = r.billing_account_id.product_id
            r.uom_id = product.uom_id.id or None

    @api.depends('property_id')
    def _get_last_reading(self):
        meter_reading_obj = self.env['mgs_billing.meter.reading']
        for r in self:
            last_reading = meter_reading_obj.search(
                [('property_id.id', '=', r.property_id.id), ('state', '=', 'posted')], limit=1, order='id DESC, date DESC')
            if last_reading:
                r.last_reading = last_reading.reading_on_date
            else:
                r.last_reading = r.property_id.initial_meter

    @api.depends('property_id')
    def _get_tenant(self):
        res_partner_obj = self.env['res.partner']
        for r in self:
            r.billing_account_id = res_partner_obj.search(
                [('property_id.id', '=', r.property_id.id)], limit=1).id
            r.average_usage = r.billing_account_id.average_usage

    @api.depends('current_reading', 'last_reading')
    def _compute_difference(self):
        for r in self:
            r.difference =round(r.current_reading - r.last_reading, 2)
