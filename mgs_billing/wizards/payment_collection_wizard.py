# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from datetime import datetime, date

_logger = logging.getLogger(__name__)


class Mgs_billingPaymentCollectionWizard(models.TransientModel):
    _name = "mgs_billing.payment.collection.wizard"
    _description = _("Payment Collection Report")

    name = fields.Char(_("Name"))

    date_from = fields.Date(default=date.today().replace(day=1))
    date_to = fields.Date(default=date.today())

    zone_id = fields.Many2many("mgs_billing.zone", string="Zone")

    collector_id = fields.Many2many("res.users",  string="Collector", domain=[('is_collector', '=', True)])

    report_type = fields.Selection([("detailed", "Detailed"),("summary", "Summary"),], string="Report Type",default="summary",required=True)
    
    
    
    
    
    def get_payment_collection(self):
        wizard_data = {
            "zone_id": [self.zone_id.id, self.zone_id.name] if self.zone_id else False,
            "collector_id": [self.collector_id.id, self.collector_id.name] if self.collector_id else False,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "report_type": self.report_type,
        }

        _logger.info("Wizard Data: %s", wizard_data)

        return self.env.ref("mgs_billing.action_payment_collection_report").report_action(self, data=wizard_data)
