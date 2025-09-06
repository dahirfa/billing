from odoo import models, fields, api
import requests
import json
from odoo.exceptions import UserError


import logging
_logger = logging.getLogger(__name__)


class Meter(models.Model):
    _inherit = 'mgs_billing.meter'

    downloader_id = fields.Many2one(
        'mgs_billing.meter.getter',
        string='Batch',
        )


class MeterGetter(models.Model):
    _name = 'mgs_billing.meter.getter'
    _description = 'Meter Batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name        = fields.Char(string="Batch #")
    meter_ids   = fields.One2many('mgs_billing.meter', 'downloader_id')
    cursor      = fields.Text(string="Cursor")
    meter_count = fields.Integer(string='Meter Count', compute='_compute_meter_count', store=True)
    
    
    @api.depends('meter_ids')
    def _compute_meter_count(self):
        for record in self:
            record.meter_count = len(record.meter_ids)    
    
    def action_trigger_cron(self):
        self.env.ref('mgs_sparkmeter.spark_unassigned_meter_cron')._trigger()
    
    @api.model
    def action_create_unassigned_meters(self):
        self.search([],limit=1)._download_meters()
        
        

    def _download_meters(self):
        # self.ensure_one()
        current_company = self.env.company
        current_company.check_sparkmeter_credentials()
        meters_obj = self.meter_ids


        total_meters_to_create = self.env.company.mgs_meters_per_click
        meters_created = 0
        meters_ = 0

        while meters_created < total_meters_to_create:
            cursor = self.cursor
            if cursor == 'None':
                return
            cursor_str = '&cursor=%s' % cursor if cursor else ''
            url = '%s/unassigned_meters?per_page=%s' % (current_company.mgs_sparkmeter_api_link, 50)
            url += cursor_str
            headers = {"Content-Type": "application/json","X-API-KEY": current_company.mgs_sparkmeter_api_key,"X-API-SECRET": current_company.mgs_sparkmeter_api_secret}
            response = requests.get(url, headers=headers, json={})
            try:
                response_dict = json.loads(response.text)
            except Exception as e:
                raise UserError("No Response Was Returned")
                
            _id = self.id
            if response.status_code != 200:
                self.message_post(body="""Failed to create meters. Status code: """ + str(response.status_code) + """ Msg: """ + response_dict['errors'][0]['details'])
            else:
                if response_dict['data'] and len(response_dict['data']) > 0:
                    response_dict['data'][-1].update({'last_line': True})
                    for line in response_dict['data']:
                        try:
                            meter = meters_obj.create({
                                'name': line['serial'],
                                'meterid': line['id'],
                                'downloader_id': _id,
                            })
                        except Exception as e:
                            self.env.cr.rollback()
                            _logger.warning("""Failed to create meter #{serial}. MSG:{msg}""".format(serial=line['serial'], msg=e))
                            if line.get('last_line', False):
                                self.cursor = str(response_dict['cursor'])
                                self.env.cr.commit()
                                continue
                            continue
                        else:
                            self.env.cr.commit()
                    self.cursor = str(response_dict['cursor'])
                    meters_created += 50
                    self.env.cr.commit()
                    if response_dict['cursor'] == None:
                        break
        if self.cursor != 'None':
            _logger.info("Trigger Next Cron")
            self.env.ref('mgs_sparkmeter.spark_unassigned_meter_cron')._trigger()

        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'type':'success',
                'message': '%s Meter has been downloaded'%meters_,
                'sticky': False}
            }
        return notification


    # def action_create_unassigned_meters(self):
    #     self.ensure_one()
    #     current_company = self.env.company
    #     current_company.check_sparkmeter_credentials()
    #     meters_obj = self.meter_ids
    #     # API endpoint and headers
    #     cursor = self.cursor
    #     cursor_str='&cursor=%s'%cursor if cursor else ''
    #     url = '%s/unassigned_meters?per_page=%s' % (current_company.mgs_sparkmeter_api_link, 50)
    #     url+cursor_str
    #     headers = {
    #         "Content-Type": "application/json",
    #         "X-API-KEY": current_company.mgs_sparkmeter_api_key,
    #         "X-API-SECRET": current_company.mgs_sparkmeter_api_secret
    #     }
    #     # Request body
    #     payload = {}
    #     response = requests.get(url, headers=headers, json=payload)
    #     response_dict = json.loads(response.text)
    #     _id=self.id
    #     if response.status_code == 200:
    #         if response_dict['data'] and len(response_dict['data']) > 0:
    #             response_dict['data'][-1].update({'last_line':True})
    #             for line in response_dict['data']:
    #                 try:
    #                     meter=meters_obj.create({
    #                         'name':line['serial'],
    #                         'meterid':line['id'],
    #                         'downloader_id':_id,
    #                     })
    #                     self.env.cr.commit()
    #                 except Exception as e:
    #                     self.message_post(body="""Failed to create meter #{serial}. MSG:{msg}""".format(serial=line['serial'], msg=e))
    #                     self.env.cr.rollback()
    #                     if line.get('last_line', False):
    #                         self.cursor = response_dict['cursor']
    #                         self.env.cr.commit()
    #                         return
    #                     continue
    #     else:
    #         self.message_post(body="""Failed to create meters. Status code: """ + str(response.status_code)+ """ Msg: """ + response_dict['errors'][0]['details'])

    # Define a smart button action
    def action_open_meters(self):
        return {
            'name': 'Meters',
            'type': 'ir.actions.act_window',
            'res_model': 'mgs_billing.meter',
            'view_mode': 'list,form',
            'domain': [('downloader_id', '=', self.id)],
            'context': "{'create': False}",
        }