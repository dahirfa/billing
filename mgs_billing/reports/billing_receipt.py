
from odoo import models, fields, api, tools


class MgsPaymentReport(models.Model):
    _name = 'mgs_billing.payment.report'
    _description = 'mgs_billing.payment.report'
    _auto = False
    _order = "id DESC"

    name = fields.Char(string='Payment #', default='/')
    date = fields.Date(string='Date')
    property_id = fields.Many2one(
        'mgs_billing.property', index=True, string='Property', required=True)
    zone_id = fields.Many2one(
        'mgs_billing.zone', store=True)
    collector_id = fields.Many2one(
        'res.partner', string='Collector', domain=[('is_collector', '=', True)])
    billing_account_id = fields.Many2one(
        'res.partner', string='Billing Account', domain=[('is_tenancy', '=', True)])
    amount_total = fields.Monetary(string='Total')
    balance = fields.Monetary(
        'Balance', related='billing_account_id.credit')
    ref = fields.Char('Reference')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one(
        'res.currency', 'Currency', related='billing_account_id.currency_id')

    # TODO: Fix this Collector Condition

    @api.model
    def _select(self):
        return """SELECT am.id id, am.name AS name, am.ref AS ref, rp.id AS billing_account_id, 
        mbz.id AS zone_id, aml.date AS date, aml.company_id AS company_id, mbp.id AS property_id, 
        -- collector.id AS collector_id, 
        '' AS collector_id, 
        sum(aml.credit-aml.debit) AS amount_total"""

    @api.model
    def _from(self):
        return """
            FROM account_move_line aml
            LEFT JOIN res_partner rp ON aml.partner_id=rp.id
            LEFT JOIN account_move am ON aml.move_id=am.id
            left join account_account as aa on aml.account_id=aa.id
            LEFT JOIN mgs_billing_property mbp ON rp.property_id=mbp.id
            LEFT JOIN mgs_billing_zone mbz ON mbp.zone_id=mbz.id
            -- LEFT JOIN res_partner collector ON mbz.collector_id=collector.id
            """

    @api.model
    def _where(self):
        return """ WHERE aa.account_type = 'asset_receivable'
        and aml.credit > 0 and rp.is_tenancy = true"""

    @api.model
    def _group_by(self):
        # return """GROUP BY am.id, am.name, am.ref, rp.id, 
        # mbz.id, aml.date, aml.company_id, mbp.id, collector.id, am.name"""
        
        return """GROUP BY am.id, am.name, am.ref, rp.id, 
        mbz.id, aml.date, aml.company_id, mbp.id, am.name"""

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute('''CREATE OR REPLACE VIEW %s AS (%s %s %s %s)''' % (
            self._table, self._select(), self._from(), self._where(), self._group_by()))
