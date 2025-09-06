
from odoo import models, fields, api, tools


class MgsSaleReport(models.Model):
    _name = 'mgs_billing.sale.report'
    _description = 'Mgs Billing Sale Report'
    _auto = False
    _order = "id DESC"

    name = fields.Char(string='Reading #', default='/')
    date = fields.Date(string='Date', default=fields.Date.today())
    current_reading = fields.Float(string="Current Reading", tracking=True)
    last_reading = fields.Float(string="Last Reading")
    difference = fields.Float(string='Difference', default=0.0)
    property_id = fields.Many2one(
        'mgs_billing.property', index=True, string='Property', required=True, tracking=True)
    zone_id = fields.Many2one(
        'mgs_billing.zone', related='property_id.zone_id', store=True)
    billing_account_id = fields.Many2one(
        'res.partner', string='Billing Account', domain=[('is_tenancy', '=', True)])
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    discount = fields.Float(string='Discount (%)',
                            digits='Discount', readonly=False)
    rate = fields.Monetary(string='Price/Unit', readonly=False)
    amount_total = fields.Monetary(string='Total')
    move_id = fields.Many2one('account.move', string='Invoice')
    # counter = fields.Integer(string='Invoice')
    product_id = fields.Many2one('product.product', string='Plan')
    meter_reading_id = fields.Many2one(
        'mgs_billing.meter.reading', string='Reading',)
    state = fields.Selection(
        [('draft', 'New'), ('posted', 'Posted'), ('cancel', 'Cancelled')], default='draft')
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'), ])

    @api.model
    def _select(self):
        return """SELECT mbr.*"""

    @api.model
    def _from(self):
        return """
            FROM mgs_billing_reading mbr
            """

    @api.model
    def _where(self):
        return """ WHERE mbr.state = 'posted'"""

    @api.model
    def _group_by(self):
        return ""

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute('''CREATE OR REPLACE VIEW %s AS (%s %s %s)''' % (
            self._table, self._select(), self._from(), self._where()))
