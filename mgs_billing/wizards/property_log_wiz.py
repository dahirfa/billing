from odoo import _, api, fields, models

class PropertyLogReport(models.Model):
    _name = 'mgs_billing.property.log.report'
    _description = 'Property Log Report'

        
    date_from = fields.Datetime(
        string='Date From',
    )
    
    
    date_to = fields.Datetime(
        string='Date To',
        default=fields.Datetime.now,
    )
    

    property_id = fields.Many2one(
        "mgs_billing.property",
        string="Property",
    )
    
    
    state = fields.Selection(
        [
            ("connected", "Connected"),
            ("disconnected", "Disconnected")
        ],
        default="connected",
    )
    
    
    
    def print_report(self):
        wizard_data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            "property_id": [self.property_id.id, self.property_id.name] if self.property_id else False,
            'state': self.state
        }

        return self.env.ref(
            "mgs_billing.action_property_log_report"
        ).report_action(self, data=wizard_data)
