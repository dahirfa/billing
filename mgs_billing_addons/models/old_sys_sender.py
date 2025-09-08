from odoo import models, fields, api
import logging
# from odoo.addons.mgs_billing.controllers.controllers import PropertyInfoApi
_logger = logging.getLogger(__name__)


class MGSNecsomAddonsSender(models.Model):
    _name = 'mgs_billing_addons.old_sys_sender'
    _description = 'Billing old_sys_sender'
    _order = "id DESC"

    name = fields.Char(string='Meter ID', required=True)
    customer_name = fields.Char(string='Customer Name')
    mgs_created_on = fields.Date(string='Created On')
    payment_mode = fields.Char(string='Payment Mode')
    payment_on = fields.Date(string='Payment On')
    sender_phone = fields.Char(string='Sender Phone')
    amount_paid = fields.Float(string='Amount Paid')
    receiver_account = fields.Char(string='Receiver Account')
    cashier = fields.Char(string='Cashier')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)
    # billing_account_id = fields.Many2one(
    #     'res.partner', string='Billing Account', compute='_get_billing_account_id', store=True)

    # @api.depends('name')
    # def _get_billing_account_id(self):
    #     for r in self:
    #         partner_obj = self.env['res.partner']
    #         domain = [('is_tenancy', '=', 'True'),
    #                   ('property_id.name', '=', r.name)]
    #         r.billing_account_id = partner_obj.search(domain, limit=1).id


class MgsSaleReport(models.Model):
    _inherit = 'mgs_billing.receivables.report'

    @api.model
    def view_portal_receivables_report(self, values, zone=None, collector=None, date=fields.Date.today(), page=1, sortby=None, filterby='current_month', search=None, groupby='none', search_in='property_name', **kw):
        partner = self.env.user.partner_id.id
        res = super(MgsSaleReport, self).view_portal_receivables_report(
            values, zone, collector, date, page, sortby, filterby, search, groupby, search_in, **kw)
        lines = []
        for line in res['data']:
            payment = self.env['account.payment'].sudo().search(
                [('partner_id', '=', line['billing_account_id']), ('mgs_sender_phone', '!=', False)], limit=2)
            if payment:
                line['sender_phone'] = '/'.join(
                    payment.mapped('mgs_sender_phone')) or ''
            else:
                sender = self.env['mgs_billing_addons.old_sys_sender'].sudo().search(
                    [('name', '=', line['property_name']), ('sender_phone', '!=', False)], limit=2)
                line['sender_phone'] = '/'.join(
                    sender.mapped('sender_phone')) or ''
            lines.append(line)

        res['data'] = lines
        return res

    @api.model
    def _select(self, date_from=fields.Date.today().replace(day=1), date_to=fields.Date.today()):
        res = super(MgsSaleReport, self)._select(date_from, date_to)
        res += ", mbp.sender_phone_utility as sender_phone"
        return res

    # @api.model
    # def _from(self):
    #     res = super(MgsSaleReport, self)._from()
    #     res += """
    #   LEFT JOIN (
    #       SELECT mgs_sender_phone, partner_id
    #       FROM account_payment
    #       WHERE mgs_sender_phone IS NOT null
    #       AND partner_id = rp.id
    #   ) ap ON rp.id = ap.partner_id
    #   LEFT JOIN (
    #       SELECT sender_phone, name
    #       FROM mgs_billing_addons_old_sys_sender
    #       WHERE sender_phone IS NOT null
    #       AND name = mbp.name
    #   ) sender ON mbp.name = sender.name

    #   """
    #     return res

    @api.model
    def _group_by(self):
        res = super(MgsSaleReport, self)._group_by()
        res += ", mbp.sender_phone_utility"
        return res


class MgsRecivablesReport(models.TransientModel):
    _inherit = 'mgs_billing.receivables.wizard'

    @api.model
    def insert_query(self):
        res = super(MgsRecivablesReport, self).insert_query()
        res += ", sender_phone"
        return res


class MgsRecivablesReport2(models.Model):
    _inherit = 'mgs_billing.receivables.wizard.line'

    sender_phone = fields.Char(
        string='Sender Phone')
    mgs_sender_phone = fields.Char()
    sender_phone_utility = fields.Char()


class MgsBillingProperty(models.Model):
    _inherit = 'mgs_billing.property'

    sender_phone_utility = fields.Char(
        string='Sender Phone', compute='_compute_sender_phone', store=True)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     # for val in vals_list:
    #     vals_list['sender_phone_utility'] = '123'
    #     res = super(MgsRecivablesReport2, self).create(vals_list)
    #     # self._compute_sender_phone()
    #     return res

    # @api.depends('billing_account_id')
    def _compute_sender_phone(self):
        for record in self:
            payment = self.env['account.payment'].search(
                [('partner_id.property_id.name', '=', record.name), ('mgs_sender_phone', '!=', False)], limit=2)
            if payment:
                record.sender_phone_utility = '/'.join(
                    payment.mapped('mgs_sender_phone')) or ''
            else:
                sender = self.env['mgs_billing_addons.old_sys_sender'].search(
                    [('name', '=', record.name), ('sender_phone', '!=', False)], limit=2)
                record.sender_phone_utility = '/'.join(
                    sender.mapped('sender_phone')) or ''


class SearchSenderNumber(models.TransientModel):
    _name = 'mgs_billing_addons.seach_sender'
    _description = 'Search Sender Number Wizard'

    # Owner form
    mgs_sender_phone = fields.Char(string='Sender Phone')
    sender_no_ids = fields.Many2many(
        'mgs_billing_addons.seach_sender.line', compute='_compute_records')

    @api.depends('mgs_sender_phone')
    def _compute_records(self):
        self.sender_no_ids = False
        if self.mgs_sender_phone:
            self.search_records()
            self.sender_no_ids = self.env['mgs_billing_addons.seach_sender.line'].sudo(
            ).search([('user_id', '=', self.env.user.id)]).ids

    def drop_records(self, user_id):
        query = "DELETE FROM mgs_billing_addons_seach_sender_line WHERE user_id=%s" % user_id
        self.env.cr.execute(query)

    def search_records(self):
        self.drop_records(self.env.user.id)
        payments = self.env['account.payment'].search(
            [('mgs_sender_phone', '!=', False), ('mgs_sender_phone', 'ilike', self.mgs_sender_phone)])

        old_sender = self.env['mgs_billing_addons.old_sys_sender'].search(
            [('sender_phone', '!=', False), ('sender_phone', 'ilike', self.mgs_sender_phone)], order='payment_on desc')
        if len(old_sender) > 0:
            for payment in old_sender:
                self.env['mgs_billing_addons.seach_sender.line'].create({
                    'name': payment.name,
                    'user_id': self.env.user.id,
                    'customer_name': payment.customer_name,
                    'payment_on': payment.payment_on,
                    'sender_phone': payment.sender_phone,
                    'amount_paid': payment.amount_paid
                })

        if len(payments) > 0:
            for payment in payments:
                self.env['mgs_billing_addons.seach_sender.line'].create({
                    'name': payment.partner_id.property_id.name,
                    'user_id': self.env.user.id,
                    'customer_name': payment.partner_id.name,
                    'payment_on': payment.date,
                    'sender_phone': payment.mgs_sender_phone,
                    'amount_paid': payment.amount
                })


class SearchSenderNumberLine(models.Model):
    _name = 'mgs_billing_addons.seach_sender.line'
    _description = 'Search Sender Number Line'
    _order = 'id desc'

    name = fields.Char(string='Meter ID')
    user_id = fields.Many2one('res.users')
    customer_name = fields.Char(string='Customer Name')
    payment_on = fields.Date(string='Payment On')
    sender_phone = fields.Char(string='Sender Phone')
    amount_paid = fields.Float(string='Amount Paid')
