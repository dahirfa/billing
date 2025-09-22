from odoo import _, api, fields, models
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)




class UnbilledMeterEvent(models.AbstractModel):
    _name = "report.mgs_unbilled_meter_event.unbilled_event_report"

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get("active_model")
        docs = self.env[model].browse(self.env.context.get("active_id"))
        
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        
      
        domain = []
        
        if data.get("zone_id"):
            zone_id = data["zone_id"][0]
            domain.append(("zone_id", "=", zone_id))
            
        if data.get("collector_id"):
            
            _logger.info(type(data.get("collector_id")))
            collector_id = data["collector_id"][0]
            domain.append(("user_id", "=", collector_id))
            
        if data.get("reason_id"):
            reason_id = data["reason_id"][0]
            domain.append(("reason_id", "=", reason_id))
        
        if date_from:
            domain.append(("date", ">=", date_from))
        if date_to:
            domain.append(("date", "<=", date_to))
        
        _logger.info("---------------")
        
        _logger.info(data.get("reason_id"))
        _logger.info(data.get("zone_id"))
        _logger.info(data.get("collector_id"))
        _logger.info(domain)
        
        results = self.env["mgs.meter.event.blocking"].search(domain)
        
        _logger.info(f"Result: {results} ")
        
        return {
            "doc_ids": docids,
            "doc_model": model,
            "docs": docs,
            "data": data,
            "results": results,
            "date_from": date_from,
            "date_to": date_to,
        }