# -*- coding: utf-8 -*-
import logging
import logging

_logger = logging.getLogger(__name__)
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date

_logger = logging.getLogger(__name__)


class MgsMeterEventWizard(models.TransientModel):
    _name = "mgs.unbilled.meter.event.wizard"
    _description = _("Meter Event Blocking")

    collector_id = fields.Many2one(
        "res.partner", string="Collector", domain=[("is_collector", "=", True)]
    )

    zone_id = fields.Many2one(
        "mgs_billing.zone",
        string="Zone",
        ondelete="restrict",
    )

    date_from = fields.Date(string="Date From", default=date.today().replace(day=1))

    date_to = fields.Date(
        string="Date To",
        default=fields.Datetime.now,
    )

    reason_id = fields.Many2one( string="Reason", comodel_name="mgs.meter.event.blocking.reason")

    def get_meter_event_wizard_data(self):

        wizard_data = {
            "zone_id": [self.zone_id.id, self.zone_id.name] if self.zone_id else False,
            "collector_id": [self.collector_id.id, self.collector_id.name] if self.collector_id else False,
            "reason_id": [self.reason_id.id, self.reason_id.name] if self.reason_id else False,
            "date_from": self.date_from,
            "date_to": self.date_to,
        }

        return self.env.ref(
            "mgs_unbilled_meter_event.action_meter_event_report"
        ).report_action(self, data=wizard_data)
