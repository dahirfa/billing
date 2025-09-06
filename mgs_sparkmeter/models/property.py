# -- coding: utf-8 --

from odoo import models, fields, api
import requests
import json
from odoo.exceptions import UserError, ValidationError




class MgsBillingPropertyAssign(models.Model):
    _name = 'mgs_sparkmeter.meter.assign'
    _description = 'Meter assignment'
    _rec_name = 'meter_id'
    
    meter_id = fields.Many2one('mgs_billing.meter',string='Meter#', required=True)
    property_id = fields.Many2one('mgs_billing.property',string='property')
    valid_state = fields.Selection([('valid', 'Valid'),('invalid','Invalid')], default='invalid', string="Valid/Invalid", compute='_compute_check', store=True)
    state = fields.Selection([('draft', 'Draft'),('posted','Registered')], default='draft' )

    @api.depends('valid_state', 'meter_id.name','property_id')
    def _compute_check(self):
        for r in self:
            r.valid_state = 'invalid'
            if r.meter_id and r.property_id:
                if r.property_id.action_get_unassigned_meters(r.meter_id.name) != "Invalid":
                    r.valid_state = 'valid'

    def action_assign(self):
        for r in self:
            result = r.property_id.action_create_sparkmeter_customer(r.meter_id)
            if result == 201:
                r.property_id.meter_type = 'smart'
                r.state = 'posted'

class MgsBillingProperty(models.Model):
    _inherit = 'mgs_billing.property'

    meter_id        = fields.Many2one('mgs_billing.meter', string='Meter')
    property_sparkmeter_customer_id = fields.Char(string='Spark customer ID', tracking=True)
    meter_serial    = fields.Char(string='Spark Meter Serial')
    serial_no       = fields.Char(string='Serial #', related='meter_id.name', store=True)
    sparkmeter_id   = fields.Char(string='Spark Meter ID')
    spark_remarks   = fields.Char()
    auto_reset      = fields.Boolean(default=False)


    def write(self, vals):
        res = super(MgsBillingProperty, self).write(vals)
        if vals.get('owner_id'):
            self.action_update_sparkmeter_customer()
        return res

    def action_create_spark_meter(self):
        meter = self.env['mgs_billing.meter']
        for r in self:
            if r.meter_serial and r.sparkmeter_id:
                meter=meter.create({
                    'name':r.meter_serial,
                    'meterid':r.sparkmeter_id,
                })
                r.meter_id=meter.id
        
    def action_reset_spark_meter(self):
        self.ensure_one()
        current_company = self.env.company
        current_company.check_sparkmeter_credentials()
        
        url = '%s/customers/%s/meter/reset' % (current_company.mgs_sparkmeter_api_link, self.property_sparkmeter_customer_id)
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": current_company.mgs_sparkmeter_api_key,
            "X-API-SECRET": current_company.mgs_sparkmeter_api_secret
        }
        payload = {}
        response = requests.get(url, headers=headers, json=payload)
        if response.status_code == 202:
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'type':'success',
                    'message': 'Reset command enqueued',
                    'sticky': False
                    }
                }
            return notification

        else:
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type':'danger',
                    'title': 'Failed',
                    'message': 'Failed to send Reset command',
                    'sticky': False
                    }
                }            
            return notification

    def action_get_unassigned_meters(self, serial):
        current_company = self.env.company
        current_company.check_sparkmeter_credentials()
        url = '%s/unassigned_meters?serial=%s' % (
            current_company.mgs_sparkmeter_api_link, serial)
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": current_company.mgs_sparkmeter_api_key,
            "X-API-SECRET": current_company.mgs_sparkmeter_api_secret
        }
        payload = {}
        response = requests.get(url, headers=headers, json=payload)
        response_dict = json.loads(response.text)
        result='Invalid'
        if response_dict['data'] and len(response_dict['data']) > 0:
            result = response_dict['data'][0]['id']
        return result

    def action_create_sparkmeter_customer(self, meter_id):
        # for r in self:
        if self.property_sparkmeter_customer_id:
            return None

        if not meter_id:
            return None

        current_company = self.env.company
        current_company.check_sparkmeter_credentials()

        owner_id = self.owner_id
        partner_id = self.env['res.partner'].search(
            [('property_id', '=', self.id), ('active', '=', True)], limit=1)
        plan_id = partner_id.product_id
        if not plan_id.property_sparkmeter_tariff_id:
            plan_id.product_tmpl_id.action_create_sparkmeter_tariff()
            
        tariff_id = plan_id.property_sparkmeter_tariff_id
        url = '%s/customers' % current_company.mgs_sparkmeter_api_link
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": current_company.mgs_sparkmeter_api_key,
            "X-API-SECRET": current_company.mgs_sparkmeter_api_secret
        }
        
        payload = {
            "name": owner_id.name,
            "code": self.name,
            # "phone_number": owner_id.mobile if self.owner_id.mobile[0] == '+' else '+' + owner_id.mobile,
            "address": owner_id.street,
            "meter_id": meter_id.meterid,
            "tariff_id": tariff_id,
            "operating_mode": "on",
            "meter_phase": "1" if self.prop_type else "3",
            "service_area_id": current_company.mgs_sparkmeter_service_area_id
        }

        
        response = requests.post(url, headers=headers, json=payload)
        try:
            response_dict = json.loads(response.text)
        except Exception as e:
            raise ValidationError("No Response for %s"% self.name)
        if response.status_code == 201:
            self.message_post(
                body="Spark : Record created successfully. Status code: " + str(response.status_code))
            self.property_sparkmeter_customer_id = response_dict['data']['id']
            self.meter_id = meter_id.id,
            meter_id.property_id=self.id
            return 201
        else:
            self.message_post(
                body="""Spark : Failed to create record. Status code: """ + str(response.status_code) + """ Msg: """ + response_dict['errors'][0]['details'])
            return 400

    def action_update_sparkmeter_customer(self):
        for r in self:
            if not r.property_sparkmeter_customer_id:
                return None
            self.env.company.check_sparkmeter_credentials()

            current_company = self.env.company
            # API endpoint and headers
            url = '%s/customers/%s' % (current_company.mgs_sparkmeter_api_link, r.property_sparkmeter_customer_id)
            headers = {
                "Content-Type": "application/json",
                "X-API-KEY": current_company.mgs_sparkmeter_api_key,
                "X-API-SECRET": current_company.mgs_sparkmeter_api_secret
            }
            owner_id = r.owner_id
            # Request body
            payload = [
                {
                    "op": "replace",
                    "path": "/name",
                    "value": owner_id.name
                },
                # {
                #     "op": "replace",
                #     "path": "/phone_number",
                #     "value": "+"+ owner_id.mobile if owner_id.mobile[0] != "+" else owner_id.mobile
                # }
            ]
            # Make POST request
            response = requests.patch(url, headers=headers, json=payload)
            response_dict = json.loads(response.text)
            # Print status code to Odoo chatter
            if response.status_code == 200:
                r.message_post(
                    body="Spark : Record update successfully. Status code: " + str(response.status_code))
                # r.property_sparkmeter_customer_id = response_dict['data']['id']
            elif response.status_code == 400:
                r.message_post(body="""Spark : Failed to update record. Status code: """ + str(response.status_code)+ """ Msg: """ + response_dict['errors'][0]['details'])

    def action_update_sparkmeter_meter_state(self, state):
        for r in self:
            if not r.property_sparkmeter_customer_id:
                return None

            self.env.company.check_sparkmeter_credentials()
            current_company = self.env.company
            # API endpoint and headers
            url = '%s/customers/%s/meter' % (current_company.mgs_sparkmeter_api_link, r.property_sparkmeter_customer_id)
            headers = {
                "Content-Type": "application/json",
                "X-API-KEY": current_company.mgs_sparkmeter_api_key,
                "X-API-SECRET": current_company.mgs_sparkmeter_api_secret
            }
            payload = [
                {
                    "op": "replace",
                    "path": "/operating_mode",
                    "value": state
                }
            ]
            response = requests.patch(url, headers=headers, json=payload)
            
            try:
                response_dict = json.loads(response.text)
            except Exception as e:
                raise ValidationError("No Response for %s"% self.name)

            if response.status_code == 200:
                self.message_post(body="Spark : Meter status updated to %s successfully. Status code: %s"  % (response.status_code, state))
            elif response.status_code == 400:
                self.message_post(body="""Spark : Failed to update meter status. Status code: """ + str(response.status_code)+ """ Msg: """ + response_dict['errors'][0]['details'])

    def _get_last_spark_reading(self):
        if self.meter_type != 'smart' or not self.property_sparkmeter_customer_id:
            raise UserError("Error: there's no smart meter associated with this property!")
        
        company = self.env.company
        url = "%s/customers/%s?&reading_details=true"%(company.mgs_sparkmeter_api_link, self.property_sparkmeter_customer_id)
        headers = {
            'X-API-KEY': company.mgs_sparkmeter_api_key,
            'X-API-SECRET': company.mgs_sparkmeter_api_secret
            
            }
        response = requests.request("GET", url, headers=headers, data={})
        response_dict = json.loads(response.text)
        if response.status_code == 200:
            last_reading =   response_dict['data']['meters'][0].get('latest_reading',False)
            return {
                'code': 200,
                'data': last_reading['energy']
            }
        else:
            return {
                'code': response.status_code,
                'msg': """Failed to fetch reading. Status code: """ + str(response.status_code)+ """ Msg: """ + response_dict['errors'][0]['details']
            }

    def action_change_state(self, state, memo):
        res = super(MgsBillingProperty, self).action_change_state(state, memo)
        if self.meter_type == "smart":
            if state == "connected": 
                self.action_update_sparkmeter_meter_state('on')
            else:
                self.action_update_sparkmeter_meter_state('off')
        return res
            
        
    
class CreateSparkmeterCustomer(models.TransientModel):
    _name = 'mgs_sparkmeter.create.customer.wizard'
    _description = 'Create Sparkmeter Customer Wizard'

    property_id = fields.Many2one('mgs_billing.property', index=True, string="Property")
    meter_id = fields.Many2one('mgs_billing.meter',string='Meter#', required=True)
    meterid = fields.Char(string='Spark Meter', compute='_compute_meterid')
    
    @api.depends('meterid', 'meter_id.name','property_id')
    def _compute_meterid(self):
        if self.meter_id and self.property_id:
            self.meterid = self.property_id.action_get_unassigned_meters(self.meter_id.name)
        else:
            self.meterid = 'Invalid'

    @api.model
    def default_get(self, fields):
        rec = super(CreateSparkmeterCustomer, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        property_id = self.env[active_model].browse(active_ids)

        rec.update({
            'property_id': property_id.id,
        })
        return rec

    def action_confirm(self):
        if not self.meter_id:
            return None

        if not self.property_id:
            return None
        self.property_id.action_create_sparkmeter_customer(self.meter_id)

# class MgsConnDescComment(models.TransientModel):
#     _inherit = 'mgs_billing.con_desc_comment.wizard'
    
#     # @api.model
#     def action_confirm(self):
#         res = super(MgsConnDescComment, self).action_confirm()
#         if self.state == 'connected':
#             self.property_id.action_update_sparkmeter_meter_state('on')
#         else:
#             self.property_id.action_update_sparkmeter_meter_state('off')
#         return res