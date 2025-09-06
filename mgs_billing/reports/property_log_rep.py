from odoo import _, api, fields, models


class PropertyLogReport(models.AbstractModel):
    _name = "report.mgs_billing.property_log_report_template"

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get("active_model")

        domain = []

        if data.get("date_from"):
            domain.append(("time", ">=", data.get("date_from")))

        if data.get("date_to"):
            domain.append(("time", "<=", data.get("date_to")))
        if data.get("property_id"):
            domain.append(("property_id", "=", data.get("property_id")[0]))
            
        if data.get('state'):
            domain.append(("state", "=", data.get('state')))

        logs = self.env["mgs_billing.property.connection.log"].search(domain)

        return {
            "data": data,
            "logs": logs,
            "model": model,
        }
