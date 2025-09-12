

from odoo import models, fields, api


class Mgs_Billing_Property(models.Model):
    _inherit = 'mgs_billing.property'
    
    unbilled_meter_event_ids = fields.One2many('mgs.meter.event.blocking', 'property_id', string='Unbilled Meter Events')
    
    unbilled_event_count = fields.Integer(
        string='Unbilled Event Count',
        compute="_compute_unbilled_event_count"
    )
    
    
    @api.depends('unbilled_meter_event_ids')
    def _compute_unbilled_event_count(self):
        for record in self:
            record.unbilled_event_count = self.env['mgs.meter.event.blocking'].search_count([('property_id', '=', self.id)])
    
         

    def action_open_meter_event_blocks(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Meter Event Blocks',
            'view_mode': 'list',
            'res_model': 'mgs.meter.event.blocking',
            'domain': [('property_id', '=', self.id)],
            'context': "{'create': True}"
        }