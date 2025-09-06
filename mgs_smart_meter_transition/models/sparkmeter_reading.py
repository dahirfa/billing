from odoo import models
   
class MgsSparkmeterReading(models.Model):
    _inherit = 'mgs_sparkmeter.reading'
    
    # def _properties_domain(self):
    #     domain = super(MgsSparkmeterReading, self)._properties_domain()
    #     # domain.append(('auto_reset','=', False))
    #     return domain

    # def _serial_not_found_error(self, serial=None):
    #     comment = super(MgsSparkmeterReading, self)._serial_not_found_error(serial)
    #     property_obj = self.env['mgs_billing.property'].search([('meter_type','=','smart'),('auto_reset','=',True),('serial_no','=',serial)])
    #     if property_obj:
    #         comment = "Property Meter Needs Reseting"
    #     return comment