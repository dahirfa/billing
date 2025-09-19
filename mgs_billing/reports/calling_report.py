from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)



class CallingReportReport(models.AbstractModel):
    _name = 'report.mgs_billing.calling_report_report'
    _description = 'Calling Report'

    @api.model
    def _lines(self, date_from, date_to, zone_id, collector_id, company_id, greater_less, greater_less_amount):
        
        
        params = [date_from, date_from, date_to,
                  date_from, date_to, date_to]
        query = """
        SELECT
            row_number() over (order by rp.id DESC) as id,
            rp.id AS billing_account_id,
            rp.name AS partner_name,
            rp.company_id AS company_id,
            mbz.name AS zone_name,
            collector.id AS collector_id,
            collector.name AS collector_name,
            mbp.name as property_name,
            rp.mobile as tenant_mobile,
            rp.alternative_number as sender_phone,
            
            COALESCE(sum(CASE WHEN aml.date < %s THEN aml.debit-aml.credit else 0.0 END), 0) AS initial_balance,
            COALESCE(sum(CASE WHEN aml.date between %s and %s THEN aml.debit else 0.0 END), 0) invoiced,
            COALESCE(sum(CASE WHEN aml.date between %s  and %s  THEN aml.credit else 0.0 END), 0) paid,
            COALESCE(sum (aml.debit-aml.credit), 0.0) balance
        FROM res_partner rp
            LEFT JOIN mgs_billing_property mbp ON rp.property_id = mbp.id
            LEFT JOIN mgs_billing_zone mbz ON mbp.zone_id = mbz.id
            LEFT JOIN res_partner collector ON mbz.collector_id=collector.id
            left join res_users as ru on ru.partner_id=collector.id
            LEFT JOIN account_move_line aml ON aml.partner_id=rp.id
            LEFT JOIN account_account AS aa ON aml.account_id = aa.id
        WHERE aa.account_type = 'asset_receivable' and aml.partner_id IS NOT NULL AND aml.date <= %s
            AND aml.parent_state = 'posted'
            AND rp.is_tenancy = True
        """

        if zone_id:
            params.append(zone_id)
            query += " AND mbz.id = %s"

        if collector_id:
            params.append(collector_id)
            query += " and collector.id = %s"

        if company_id:
            params.append(company_id)
            query += " and aml.company_id = %s"

        query += """
        GROUP BY rp.id, rp.company_id, mbz.id, collector.id, mbp.name, rp.mobile, rp.name"""
        query += " HAVING COALESCE(sum (aml.debit-aml.credit), 0.0) " + \
            "> " + str(greater_less_amount) if greater_less == 'Greater' else "< " + \
            str(greater_less_amount)

        self.env.cr.execute(query, tuple(params))
        lines = []
        res = self.env.cr.dictfetchall()
        
        
        _logger.info(res)
        
        return res
      

    @ api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'date_from': data['form']['date_from'],
            'date_to': data['form']['date_to'],
            'zone_id': data['form']['zone_id'],
            'collector_id': data['form']['collector_id'],
            'states': data['form']['states'],
            'company_id': self.env['res.company'].search([('id', '=', data['form']['company_id'][0])]),
            'greater_less': data['form']['greater_less'],
            'greater_less_amount': data['form']['greater_less_amount'],
            'lines': self._lines,
        }
