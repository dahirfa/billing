

from odoo import models, fields, api


class Mgs_Billing_Property(models.Model):
    _inherit = 'mgs_billing.property'

    def action_open_meter_event_blocks(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Meter Event Blocks',
            'view_mode': 'list',
            'res_model': 'mgs.meter.event.blocking',
            'domain': [('property_id', '=', self.id)],
            'context': "{'create': True}"
        }