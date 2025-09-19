from odoo import models, fields, api


class MGSBillingResetMeter(models.Model):
    _name = 'mgs_billing.reset.meter'
    _description = 'Billing Reset Meter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id DESC"

    name = fields.Char(string='Reading #', default='/', index=True)
    property_id = fields.Many2one(
        'mgs_billing.property', string='Property', index=True, required=True)
    billing_account_id = fields.Many2one(
        'res.partner', domain=[('is_tenancy', '=', True)], string='Billing Account', compute='_get_billing_account_id', store=True)
    reading = fields.Integer(string='Meter', required=True)
    date = fields.Date(
        string='Date', default=fields.Date.today(), required=True)
    make_credit_note = fields.Boolean(default=False)
    move_id = fields.Many2one('account.move', index=True, string='Credit Note')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed')], required=True, default='draft')

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True, default=lambda self: self.env.company.currency_id.id)

    @api.depends('property_id')
    def _get_billing_account_id(self):
        partner_obj = self.env['res.partner']
        for r in self:
            domain = [('is_tenancy', '=', True),
                      ('property_id', '=', r.property_id.id)]
            r.billing_account_id = partner_obj.search(domain, limit=1).id

    def action_confirm(self):
        meter_reading_obj = self.env['mgs_billing.meter.reading']
        for r in self:
            query = """
            INSERT INTO mgs_billing_meter_reading
            (date, property_id, reading_on_date, comment, state, 
            create_date, create_uid, write_date, write_uid)
            VALUES ('%s', %s, %s, 'Meter Reset', 'posted', '%s', %s, '%s', %s);
            """ % (r.date, r.property_id.id, r.reading, fields.datetime.now(), self.env.user.id, fields.datetime.now(), self.env.user.id)
           
            self.env.cr.execute(query)
            r.state = 'confirm'


    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'mgs_billing.reset_reading') or '/'
        return super(MGSBillingResetMeter, self).create(vals_list)