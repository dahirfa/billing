from odoo import _, api, fields, models
import logging

_logger = logging.getLogger(__name__)

class PaymentCollectionReport(models.AbstractModel):
    _name = "report.mgs_billing.payment_collection_report"

    @api.model
    def _get_report_values(self, docids, data=None):
        where = ""
        if data.get("date_from"):
            where += f" AND aml.date >= '{data['date_from']}' "
        if data.get("date_to"):
            where += f" AND aml.date <= '{data['date_to']}' "
        if data.get("collector_id"):
            where += f" AND mbz.collector_id = {data['collector_id'][0]} "
        if data.get("zone_id"):
            where += f" AND mbz.id = {data['zone_id'][0]} "

        base_select = """
            COALESCE(sum(CASE WHEN aml.date < '%(date_from)s' THEN aml.debit-aml.credit ELSE 0.0 END), 0) AS initial_balance,
            COALESCE(sum(CASE WHEN aml.date BETWEEN '%(date_from)s' AND '%(date_to)s' THEN aml.debit ELSE 0.0 END), 0) AS invoiced,
            COALESCE(sum(CASE WHEN aml.date BETWEEN '%(date_from)s' AND '%(date_to)s' THEN aml.credit ELSE 0.0 END), 0) AS paid,
            COALESCE(sum(aml.debit-aml.credit), 0.0) AS balance
        """ % {
            "date_from": data["date_from"],
            "date_to": data["date_to"],
        }

        base_from = f"""
            FROM res_partner rp
                LEFT JOIN mgs_billing_property mbp ON rp.property_id = mbp.id
                LEFT JOIN mgs_billing_zone mbz ON mbp.zone_id = mbz.id
                LEFT JOIN res_partner collector ON mbz.collector_id=collector.id
                LEFT JOIN res_users ru ON ru.partner_id=collector.id
                LEFT JOIN account_move_line aml ON aml.partner_id=rp.id
                LEFT JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.account_type = 'asset_receivable'
                AND aml.partner_id IS NOT NULL
                AND aml.date <= '{data['date_to']}'
                AND aml.parent_state = 'posted'
                AND rp.is_tenancy = True
                AND mbp.state = 'connected'
                {where}
        """

        if data.get("report_type") == "summary":
            select_clause = f"""
                SELECT
                    mbz.id AS zone_id,
                    mbz.name AS zone_name,
                    collector.id AS collector_id,
                    collector.name AS collector_name,
                    {base_select}
            """
            group_clause = """
                GROUP BY mbz.id, mbz.name, collector.id, collector.name
                ORDER BY mbz.name
            """
        else:
            select_clause = f"""
                SELECT
                    rp.id AS billing_account_id,
                    rp.complete_name AS display_name,
                    rp.company_id AS company_id,
                    mbz.id AS zone_id,
                    mbz.name AS zone_name,
                    collector.id AS collector_id,
                    collector.name AS collector_name,
                    mbp.name AS property_name,
                    rp.mobile AS partner_mobile,
                    aml.date AS move_date,
                    {base_select}
            """
            group_clause = """
                GROUP BY rp.id, rp.company_id, rp.complete_name, rp.mobile,
                         mbz.id, mbz.name, collector.id, collector.name, mbp.name, move_date
                ORDER BY mbz.name, rp.complete_name
            """

        query = f"{select_clause} {base_from} {group_clause}"

        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()
        
        
        if data.get("report_type") == "detailed":
            # Group records by zone
            grouped = {}
            for rec in records:
                zone_name = rec["zone_name"] or "No Zone"
                if zone_name not in grouped:
                    grouped[zone_name] = []
                grouped[zone_name].append(rec)
            docs = grouped
        else:
            # Summary is just a flat list
            docs = records

        _logger.info(docs)

        return {
            "data": data,
            "docs": docs,
        }