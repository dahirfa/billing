from odoo import _, api, fields, models
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class GetMonthesDue(models.AbstractModel):
    _name = "report.mgs_billing.get_monthes_due_report"

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get("active_model")
        docs = self.env[model].browse(self.env.context.get("active_id"))

        monthes_due = data.get("monthes_due", 0)

        current_date = fields.Date.context_today(self)
        months_ago = current_date - timedelta(days=monthes_due * 30)

        months_between_dates = [
            (months_ago + timedelta(days=day)).strftime("%B")
            for day in range((current_date - months_ago).days + 1)
            if (months_ago + timedelta(days=day)).month
            != (months_ago + timedelta(days=day + 1)).month
        ]
        

        where = ""
        if data.get("collector_id", False):
            where += " AND mbz.collector_id = %s " % data.get("collector_id")[0]

        if data.get("zone_id", False):
            where += " AND mbz.id = %s " % data.get("zone_id")[0]

        if data.get("meter_type", False):
            where += " AND mbp.meter_type = '%s' " % data.get("meter_type")

        if data.get("state", False):
            where += " AND mbp.state = '%s' " % data.get("state")

        query = """
                SELECT aml.partner_id, rp.complete_name, rp.mobile, mbp.name, mbz.name, COALESCE(SUM(aml.debit - aml.credit), 0), lams.amount, lams.am_count
                FROM account_move_line aml
                LEFT JOIN account_account aa ON aml.account_id = aa.id
                LEFT JOIN res_partner rp ON aml.partner_id = rp.id
                LEFT JOIN mgs_billing_property mbp ON rp.property_id = mbp.id
                LEFT JOIN mgs_billing_zone mbz ON mbz.id = mbp.zone_id
                

                LEFT JOIN (
                SELECT count(*) as am_count, am.partner_id, COALESCE(SUM(am.amount_total), 0) as amount
                
                FROM account_move am
                LEFT JOIN res_partner srp ON am.partner_id = srp.id
                WHERE am.state = 'posted' 
                AND am.reading_id IS NOT NULL 
                --AND am.invoice_date >= '%s'
                AND am.payment_state = 'not_paid'
                AND srp.is_tenancy = TRUE
                GROUP BY am.partner_id
                ) lams ON lams.partner_id = aml.partner_id
                
                
                WHERE aa.account_type = 'asset_receivable' %s
                AND aml.parent_state = 'posted' AND rp.is_tenancy = TRUE AND lams.am_count >= %s
                GROUP BY aml.partner_id, lams.amount, rp.complete_name, rp.mobile, mbp.name, mbz.name, lams.am_count
                -- HAVING lams.amount < COALESCE(SUM(aml.debit - aml.credit), 0) ;
                
        """ % tuple(
            [months_ago, where, monthes_due]
        )

        self.env.cr.execute(query)

        records = self._cr.fetchall()

        return {"data": data, "records": records, "months": months_between_dates}
