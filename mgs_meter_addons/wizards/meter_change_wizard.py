from odoo import models, fields, api
from odoo.exceptions import UserError


class Mgs_Assign_Meter(models.TransientModel):
    _name = 'mgs_meter.create.customer.wizard'
    _description = 'Assign/Change Meter Wizard'

    property_id = fields.Many2one('mgs_billing.property', index=True, string="Property")
    meter_id = fields.Many2one('mgs_billing.meter',string='Meter#', required=True)
    meterid = fields.Char(string='Meter', compute='_compute_meterid')

    @api.depends('meter_id', 'property_id')
    def _compute_meterid(self):
        for record in self:
            if record.meter_id and record.property_id:
                # Check if the selected meter is already assigned to another property
                existing_property = self.env['mgs_billing.property'].search([
                    ('meter_serial_id', '=', record.meter_id.id)                    
                ], limit=1)
                
                if existing_property:
                    record.meterid = 'Invalid'
                else:
                    record.meterid = record.meter_id.name or 'Valid'
            else:
                record.meterid = 'Invalid'

    @api.model
    def default_get(self, fields):
        rec = super(Mgs_Assign_Meter, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        
        if active_model and active_ids:
            property_id = self.env[active_model].browse(active_ids[0])  # Get first record
            rec.update({
                'property_id': property_id.id,
            })
        return rec

    def action_confirm(self):
        """Assign meter to property if valid, otherwise show error"""
        self.ensure_one()
        
        if not self.meter_id or not self.property_id:
            raise UserError("Please select both a meter and property.")
        
        # Check if meter is already assigned to another property
        existing_property = self.env['mgs_billing.property'].search([
            ('meter_serial_id', '=', self.meter_id.id),
            ('id', '!=', self.property_id.id)
        ], limit=1)
        
        if existing_property:
            raise UserError(
                f"Meter '{self.meter_id.name}' is already assigned to property '{existing_property.name}'. "
                f"Please select a different meter or unassign it from the existing property first."
            )
        
        if self.property_id.meter_serial_id:
            self.property_id.meter_serial_id.property_id = False
        
        # Update the property with the selected meter
        self.property_id.write({
            'meter_serial_id': self.meter_id.id
        })
        
        self.meter_id.property_id = self.property_id.id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f"Meter '{self.meter_id.name}' has been successfully assigned to property '{self.property_id.name}'.",
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }




