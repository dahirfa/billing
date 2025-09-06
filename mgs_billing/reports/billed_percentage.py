from odoo import models, fields, api, tools


class MgsSaleReport(models.AbstractModel):
    _name = 'report.mgs_billing.percentage_report'
    _description = 'Billing Percetage Report'

    @api.model
    def _get_total_customers_billed(self, date_from, date_to, zone_id, company_id):
        params = [date_from, date_to]
        query = """
        SELECT count(*) as total_billed_customers
        FROM mgs_billing_reading mbr
        WHERE mbr.date BETWEEN %s AND %s
        AND mbr.state='posted'"""

        if zone_id:
            params.append(zone_id)
            query += " AND mbr.zone_id = %s"

        if company_id:
            params.append(company_id)
            query += " AND mbr.company_id = %s"

        self.env.cr.execute(query, tuple(params))

        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    @api.model
    def _lines(self, date_from, date_to, zone_id, collector_id, company_id):
        params = []
        lines = []
        query = """SELECT
        row_number() over (order by mbz.id DESC) as id,
        mbz.id AS zone_id,
        mbz.name AS zone_name,
        mbz.collector_id AS collector_id,
        rp.name AS collector_name,
        mbz.company_id AS company_id,
        COALESCE(mbz.active_counter, 0) AS  property_count
        FROM mgs_billing_zone AS mbz
        LEFT JOIN mgs_billing_reading mbr ON mbr.zone_id=mbz.id 
        LEFT JOIN res_partner rp on mbz.collector_id=rp.id
        WHERE mbz.counter > 0
        """

        if zone_id:
            params.append(zone_id)
            query += " AND mbz.id = %s"

        if collector_id:
            params.append(collector_id)
            query += " AND mbz.collector_id = %s"

        if company_id:
            params.append(company_id)
            query += " AND mbz.company_id = %s"

        query += "GROUP BY mbz.id, mbz.collector_id,mbz.company_id,rp.name"

        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        for r in res:
            r['billed_count'] = self._get_total_customers_billed(
                date_from, date_to, r['zone_id'], r['company_id'])

            r['percentage'] = 0
            if r['property_count'] and r['billed_count']:
                r['percentage'] = (r['billed_count'] * 100) / \
                    r['property_count']
            lines.append(r)
        return lines

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        # def _lines(self, date_from, date_to, zone_id, collector_id, company_id):

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'date_from': data['form']['date_from'],
            'date_to': data['form']['date_to'],
            'zone_id': data['form']['zone_id'],
            'collector_id': data['form']['collector_id'],
            'company_id': self.env['res.company'].search([('id', '=', data['form']['company_id'][0])]),
            'lines': self._lines,
        }
