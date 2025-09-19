from odoo import _, api, fields, models


class GetMonthesDue(models.TransientModel):
    _name = "get.monthes.due"
    _description = "Mgs Billing Get MOnthes Due"

    collector_id = fields.Many2one("res.partner", string="Collector", domain=[("is_collector", "=", True)])

    zone_id = fields.Many2one(
        "mgs_billing.zone",
        string="Zone",
        ondelete="restrict",
    )
    
    

    monthes_due = fields.Integer(string="Monthes Due",  default=0)

    state = fields.Selection(
        [
            ("connected", "Connected"),
            ("disconnected", "Disconnected")            
        ],
        default="connected",
    )

    meter_type = fields.Selection(
        [("normal", "Normal"), ("smart", "Smart")], default="normal", required=True
    )

    def get_monthes_due(self):
        
        wizard_data = {
            'zone_id': [self.zone_id.id, self.zone_id.name] if self.zone_id else False,
            'collector_id': [self.collector_id.id, self.collector_id.name] if self.collector_id else False,
            "monthes_due": self.monthes_due,
            "state": self.state,
            "meter_type": self.meter_type,
        }

        return self.env.ref(
            "mgs_billing.action_report_get_monthes_due"
        ).report_action(self, data=wizard_data)
