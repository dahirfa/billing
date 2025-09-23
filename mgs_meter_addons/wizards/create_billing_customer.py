# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.addons.phone_validation.tools import phone_validation


class CreateCustomerWizardInherit(models.TransientModel):
    _inherit = 'mgs_billing.customer.wizard'
    _description = 'Create Customer Wizard'


    meter_serial = fields.Char(string='Meter Serial')
    meter_type  = fields.Selection([('smart', 'Smart'), ('normal', 'Normal')], tracking=1, default='normal')


    def _create_meter(self, meter, property_id, meter_type):
        vals = {
            "name":meter,
            'property_id': property_id,
            "meter_type": meter_type,
        }
        meter = self.env['mgs_billing.meter'].create(vals)
        
        return meter
   
    def action_proceed(self):     
        property_id = super(CreateCustomerWizardInherit, self).action_proceed()    
        
        meter = self._create_meter(self.meter_serial, property_id.id, property_id.meter_type)
        
        property_id.meter_serial_id = meter.id
        
        return property_id
    
