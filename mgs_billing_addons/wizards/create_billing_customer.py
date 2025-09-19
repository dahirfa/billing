# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.addons.phone_validation.tools import phone_validation


class CreateCustomerWizardInherit(models.TransientModel):
    _inheirt = 'mgs_billing.customer.wizard'
    _description = 'Create Customer Wizard'


    pipe_extention = fields.Char(string='pipe extention')
    pipe_type = fields.Char(string='Pipe Type')
    meter_category = fields.Char(string='Meter Category')


    @api.model
    def default_get(self, fields):
        rec = super(CreateCustomerWizardInherit, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        lead_id = self.env[active_model].browse(active_ids)

        rec.update({
            "pipe_extention":lead_id.pipe_extention,
            "pipe_type": lead_id.pipe_type,
            "meter_category": lead_id.meter_category,
        })

        return rec

        
        
    def _prepare_property_vals(self):
        vals = super()._prepare_property_vals()
        vals.update({
            "pipe_extention": self.pipe_extention,
            "pipe_type": self.pipe_type,
            "meter_category": self.meter_category,
        })
        return vals