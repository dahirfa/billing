from odoo import models, fields, api
from datetime import datetime, date
import requests
import json
class BulkSMS(models.Model):
    _name = 'mgs.send.bulk.sms'
    _description = 'Bulk SMS Sending'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(default=lambda self: "New",
        required=True,
        readonly=True,)
    zone_id = fields.Many2one('mgs_billing.zone', string='Zone', required=True, tracking=True)
    message = fields.Text(string='Message',  tracking=True)
    
    
    date = fields.Date(default=fields.Date.today, required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], default='draft', string='Status', required=True, tracking=True)
    log_ids = fields.One2many('mgs.bulk.sms.log', 'sms_id', string='Logs')  
    log_count = fields.Integer(string='Logs Count', compute='_compute_log_count', store=False)

    @api.depends('log_ids')
    def _compute_log_count(self):
        for record in self:
            record.log_count = len(record.log_ids)
            
    @api.model
    def create(self, vals):
        current_year = datetime.now().strftime('%Y')
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('mgs.send.bulk.sms') % {'year': current_year}
        return super(BulkSMS, self).create(vals)
    
    def process_bulk_sms(self):
        for r in self.zone_id.property_ids:
            
                record = self.env['mgs.bulk.sms.log'].create({
                    'partner_id': r.owner_id.id,  
                    'zone_id': r.zone_id.id,  
                    'sms_id': self.id,
                    'message': self.message,
                })
                record.send_sms()
        self.write({'state': 'done'})
        
    def send_fee_remaining_sms(self):
        
        properties_in_zone = self.env['mgs_billing.property'].search([
            ('zone_id', '=', self.zone_id.id)
        ])
        property_ids = properties_in_zone.ids

       
        partners = self.env['res.partner'].search([
            ('property_id', 'in', property_ids)  
        ])

        for partner in partners:
            if partner.mgs_credit > 0:
                record = self.env['mgs.bulk.sms.log'].create({
                        'partner_id': partner.customer_id.id,  
                        'zone_id': self.zone_id.id,  
                        'sms_id': self.id,
                        'message': f"Macmiil bixi lacagta korontada ${partner.mgs_credit} ee lagu leeyahay guriga numberkisu yahay {partner.property_id.name} ee {partner.customer_id.name}.",
                        })
                record.send_sms()
        self.write({'state': 'done'})

    def action_view_logs(self):
        return {
            'name': 'Bulk SMS Logs',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'mgs.bulk.sms.log',
            'domain': [('sms_id', '=', self.id)],
            'context': {'default_sms_id': self.id},
        }

class BulkSMSLog(models.Model):
    _name = 'mgs.bulk.sms.log'
    _description = 'Bulk SMS Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "datetime"
    
    datetime = fields.Datetime(string='Datetime', default=fields.Datetime.now, required=True)
    response = fields.Text(string='Response')
    partner_id = fields.Many2one('mgs_billing.billing_customer', string='Partner', required=True)
    mobile = fields.Char(related='partner_id.mobile')  
    status = fields.Selection([
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ], string='Status')
    zone_id = fields.Many2one('mgs_billing.zone', string='Zone', required=True)
    sms_id = fields.Many2one('mgs.send.bulk.sms', string='Bulk SMS', required=True)
    message = fields.Text()
    
    def send_sms(self):
        if not self.mobile:
            self.message_post(body='This partner has no mobile number')
            return 'This partner has no mobile number'
        
        sender = self.env.company.mgs_golis_sender
        token = self.env.company.mgs_golis_token

        url = "https://easytechapp.com/api/v3/sms/send?type=plain&message=%s&sender_id=%s&recipient=%s" % (
            self.message, sender, self.mobile)
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token,
            'Cookie': 'cookiesession1=678A8C55KMNOPQRSTUVWXYZABCDEF7C8'}
        try:
            response = requests.post(
                url, headers=headers, data=payload, timeout=10)
            response = json.loads(response.text)
            self.write({'response': response})

            if response['status'] != "success":
                self.write({'status': 'failed'})
                return 'failed to send sms'
            if response['status'] == "success":
                self.write({'status': 'sent'})
                return 'the sms was sent successfully'
        except Exception as e:
            self.message_post(body=e)
            return f"failed to send sms: {str(e)}"
    
    
    
