from odoo import models, fields, api
import requests
import json
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)
from datetime import date
from dateutil.relativedelta import relativedelta


class MgsSparkReadingFailLog(models.Model):
    _name       = 'mgs_sparkmeter.reading.log'
    _description= 'Sparkmeter Reading Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order      = "id DESC"
    
    name                = fields.Char(string='Ref')
    comment             = fields.Char()
    state               = fields.Selection([('posted', 'Posted'), ('queue', 'In Queue'), ('fail', 'failed')], default = 'queue')
    eligible            = fields.Boolean(default=True)
    has_last_reading    = fields.Boolean(default=False)
    checked             = fields.Boolean(default=False)
    spark_reading_id    = fields.Many2one('mgs_sparkmeter.reading')
    property_id         = fields.Many2one('mgs_billing.property')
    zone_id             = fields.Many2one(comodel_name='mgs_billing.zone', related="property_id.zone_id", store=True)
    reading_id          = fields.Many2one('mgs_billing.reading')
    date                = fields.Date(default=fields.Date.today(), required=True, tracking=1, readonly=True)
    
    #SPARK: All The Following Fields Will be fetched from sparkmeter
    customer_name       = fields.Char()
    customerid          = fields.Char()
    code                = fields.Char(string='Home #')
   
    serial              = fields.Char(string='Meter Serial')
    meter_state         = fields.Selection([('on', 'On'), ('off', 'Off'), ('auto', 'Auto')])
    
    latest_reading      = fields.Float()
    heartbeat_start     = fields.Datetime()
    heartbeat_end       = fields.Datetime()
    

    tariffid            = fields.Char()
    origional_json      = fields.Json()
    
    
    def action_create_reading(self):
        reading_obj = self.env['mgs_billing.reading']
        for r in self:
            r._create_reading(reading_obj)
        
    def _create_reading(self, reading_obj):
        reading = reading_obj.create({
            'property_id':self.property_id.id,
            'current_reading': self.latest_reading,
            'spark_reading_id': self.spark_reading_id.id,
            'spark_reading_log_id': self.id,
        })
        reading.action_confirm()
        self.write({'reading_id':reading.id, 'state':'posted'})
        
        
    def search_properties(self, properties_domain=[]):
        property_obj = self.env['mgs_billing.property']
        if not properties_domain:
            properties_domain= self.env['mgs_sparkmeter.reading']._properties_domain()
        for r in self:
            domain = properties_domain
            if not r.serial:
                r.property_id = None
                continue
            prop = property_obj.search(domain + [('serial_no','=',r.serial)], limit=1)
            r.property_id = prop.id if prop else None
            
    
    def _mark_non_eligible(self, reading = None):        
        logs = self
        logs = logs.filtered(lambda x: x.checked == False)        

        # has no last reading
        logs.filtered(lambda x: x.has_last_reading != True).write({'eligible':False, 'comment': "No Reading"})
        
        # Property Not Found
        logs.filtered(lambda x: not x.property_id ).write({'eligible':False, 'comment': "Serial # Not Found"})
        
        # Property Needs reseting
        logs.filtered(lambda x: x.property_id and  x.property_id.auto_reset == True).write({'eligible':False, 'comment': "Property Needs Reseting"})

        # Disconnected or prepaid properties
        logs.filtered(lambda x: x.meter_state in ('on', 'auto')).write({'eligible':False, 'comment': "Disconnected Meter"})
        active = self.env.context.get('active_id', [])
        spark_reading_id = self.env['mgs_sparkmeter.reading'].browse(active) if not reading else reading
        
        allowed_reg_date = spark_reading_id.start_date.replace(day=int(self.env.company.allowed_reg_date))
        
        # Recently Registered
        logs.filtered(lambda x: x.property_id != False
                      and x.property_id.connection_date
                      and x.property_id.connection_date.date() >= allowed_reg_date).write({'eligible':False, 'comment': "Recently Registered Property"})
                
        # Old Last Reading
        days=self.env.company.mgs_sparkmeter_prb
        oldlogs=logs.filtered(lambda x: x.heartbeat_end)
        _logger.warning(oldlogs.mapped('heartbeat_end'))
        oldlogs.filtered(lambda x: x.heartbeat_end.date() < x.date  - relativedelta(days=days)).write({
            'eligible':False,
            'checked':True,
            'comment': f"Last reading is before the allowed period - {days} days",
            })
        logs.write({'checked':True})
        
        
    
    def mark_non_eligible(self):        
        self._mark_non_eligible()
        
    

    
    def action_retry(self):
        property_obj = self.env['mgs_billing.property']
        reading_obj = self.env['mgs_billing.reading']
        for r in self:
            prop = property_obj.search([('serial_no','=',r.serial)])
            if len(prop.ids)!= 1:
                raise ValidationError(f"There's more than 1 property with this serial : {r.serial}")
            else:
                lr=prop._get_last_spark_reading()
                try:
                    reading=reading_obj.create({
                        'property_id':prop.id,
                        'current_reading': lr['data'],
                        'spark_reading_id': r.spark_reading_id.id,
                    })
                    reading.action_confirm()
                except Exception as e:
                    raise ValidationError(e)
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'type':'success',
                        'message': 'Meter Reading Created Successfully',
                        'sticky': False}
                    }
                r.unlink()
                return notification
            
class MgsSparkmeterReading(models.Model):
    _name = 'mgs_sparkmeter.reading'
    _description = 'Sparkmeter Reading'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id DESC"

    name            = fields.Char(string='Ref', copy=False, default='/', readonly=True)
    date            = fields.Date(default=fields.Date.today(), required=True, tracking=1, readonly=True)
    start_date      = fields.Date(string='Period Start Date', compute='_compute_period', store=True)
    end_date        = fields.Date(string='Period End Date', compute='_compute_period', store=True)
    reading_ids     = fields.One2many('mgs_billing.reading', 'spark_reading_id', copy=False)
    fail_log_ids    = fields.One2many('mgs_sparkmeter.reading.log', 'spark_reading_id', copy=False)
    log_ids         = fields.One2many('mgs_sparkmeter.reading.log', 'spark_reading_id', copy=False)
    reading_count   = fields.Integer(string='No of Readings', default=0, compute='_compute_reading_count')
    log_count       = fields.Integer(string='Failed', default=0, compute='_compute_log_count')
    fail_log_count  = fields.Integer(string='Failed', default=0, compute='_compute_log_count')
    to_bill_count   = fields.Integer(compute='_compute_to_bill_count', string="To Bill", store=True, copy=False)
    progress        = fields.Float(compute='_compute_progress', store=True, copy=False)
    cursor          = fields.Text()
    state           = fields.Selection([('queue','In Queue'),('done', 'Done')], default='queue')

    @api.depends('date')
    def _compute_period(self):
        company = self.env.company
        start, end = company.billing_period_start, company.billing_period_end
        for r in self:
            if r.date:
                r.start_date, r.end_date = date_utils.get_billing_start_and_end_dates(r.date, start, end)
            else:
                r.start_date, r.end_date = None, None
    
    def action_trigger_cron(self):
        self.env.ref('mgs_sparkmeter.spark_cron')._trigger()
        
    def action_trigger_validation_cron(self):
        self.env.ref('mgs_sparkmeter.spark_validation_cron')._trigger()



    def send_email_to_followers(self, e, mtype='fail'):
        # Get the followers of the record
        followers = self.message_follower_ids
        if mtype == 'fail':
            subject = "SparkMeter Reading Failure Notification"
            body = f"The Automatic Billing of Sparkmeter encountered an Error While Processing Readings.\nDetails: {e}"
        else:
            subject = "SparkMeter Auto-Reading is Complete!"
            body = f"The Automatic Billing of Sparkmeter Is Completed. Please Review The Readings As Soon As Possible."
        self.message_post(
            body=body,
            subject=subject,
            subtype_xmlid ="mail.mt_comment",
            partner_ids=[follower.partner_id.id for follower in followers], auto_delete=False)

    def _properties_domain(self):
        domain = [('meter_type','=','smart')]
        return domain

    @api.model
    def action_confirm_spark_readings(self, batch_size=50):
        current_date            = date.today()
        company                 = self.env.company
        start, end              = company.billing_period_start, company.billing_period_end
        start_date, end_date    = date_utils.get_billing_start_and_end_dates(current_date, start, end)
        spark_reading           = self.search([('start_date','=',start_date),('end_date','=',end_date), ('cursor','=','Done'), ('state','=', 'queue')], limit=1)
        if not spark_reading:
            return
        
        needs_checking          = spark_reading.log_ids.filtered(lambda x: x.checked == False and x.eligible and x.state == 'queue')[:batch_size + 1]
        _id                     = spark_reading.id
        next_cron_trigger       = False

        if len(spark_reading.log_ids.filtered(lambda x: x.eligible and x.state == 'queue')[:batch_size + 1]) > 50:
            next_cron_trigger   = True
            
        if needs_checking:
            needs_checking.search_properties(self._properties_domain())
            needs_checking._mark_non_eligible(spark_reading)
            self.env.cr.commit()
        
        log = spark_reading.log_ids.filtered(lambda x: x.checked and x.eligible and x.state == 'queue')[:batch_size]
        reading_obj = self.env['mgs_billing.reading']
        for record in log:
            try:
                reading = reading_obj.create({
                    'property_id':record.property_id.id,
                    'current_reading': record.latest_reading,
                    'spark_reading_id': _id,
                    'spark_reading_log_id': record.id,
                })
                reading.action_confirm()
            except Exception as e:
                self.env.cr.rollback()
                record.write({'state':'fail','comment':e})
                self.env.cr.commit()
            else:
                record.write({'reading_id':reading.id, 'state':'posted'})
                self.env.cr.commit()
        if  next_cron_trigger:
            _logger.info("Trigger Next Validation Cron")
            self.env.ref('mgs_sparkmeter.spark_validation_cron')._trigger()
            return
        else:
            if spark_reading.cursor != 'Done':
                return
            else:
                spark_reading.state = 'done'
                self.env.cr.commit()
                spark_reading.send_email_to_followers(None, 'success')

    
    @api.model
    def action_create_spark_readings(self, batch_size=50):
        current_date            = date.today()
        company                 = self.env.company
        start, end              = company.billing_period_start, company.billing_period_end
        start_date, end_date    = date_utils.get_billing_start_and_end_dates(current_date, start, end)
        spark_reading           = self.search([('start_date','=',start_date),('end_date','=',end_date)], limit=1)
        if not spark_reading:
            spark_reading=self.create({'date':current_date})
        cursor                  = spark_reading.cursor
        if spark_reading.cursor == 'Done':
            raise UserError('Readings Are Done For This Period')
        log                     = spark_reading.log_ids
        _id                     = spark_reading.id
        cursor_str              = '&cursor=%s'%cursor if cursor else ''
        url                     = "%s/customers?per_page=%s&reading_details=true%s"%(company.mgs_sparkmeter_api_link, batch_size, cursor_str)
        headers = {
            'X-API-KEY': company.mgs_sparkmeter_api_key,
            'X-API-SECRET': company.mgs_sparkmeter_api_secret
            }
        response                = requests.request("GET", url, headers=headers, data={})
        _logger.info(url)
        try:
            response_dict = json.loads(response.text)
        except Exception as e:
            spark_reading.send_email_to_followers("No Response From Sparkmeter API")
            raise ValidationError("No Response")

        if response.status_code != 200:
            spark_reading.send_email_to_followers(response_dict['errors'][0]['details'])
            spark_reading.message_post(body="""Failed to create reading. Status code: """ + str(response.status_code)+ """ Msg: """ + response_dict['errors'][0]['details'])
        else:
            if len(response_dict['data']) > 0:
                response_dict['data'][-1].update({'last_line':True})
            for line in response_dict['data']:
                record = {
                    "spark_reading_id"  : _id,
                    "customer_name"     : line['name'],
                    "customerid"        : line['id'],
                    "code"              : line['code'],
                    "origional_json"    : line
                    }
                if line.get('meters', False):
                    meter =  line['meters'][0]
                    record.update({                    
                                   "serial"     : meter['serial'],
                                   "meter_state": meter['operating_mode'],
                                   "tariffid"  : meter['tariff_id']
                                   })
                    if meter.get('latest_reading', False):
                        latest_reading = meter['latest_reading']
                        heartbeat_start = datetime.strptime(latest_reading['heartbeat_start'], "%Y-%m-%dT%H:%M:%S")
                        heartbeat_end = datetime.strptime(latest_reading['heartbeat_end'], "%Y-%m-%dT%H:%M:%S")
                        record.update({
                            "has_last_reading": True,
                            "latest_reading" : latest_reading['energy'],
                            "heartbeat_start": heartbeat_start,
                            "heartbeat_end"  : heartbeat_end,
                                       })
                        
                try:
                    log.create(record)
                except Exception as e:
                    self.env.cr.rollback()
                    log.create({"spark_reading_id": _id,'origional_json': line, 'comment':f"Failed to create record - {e}"})
                    self.env.cr.commit()
                else:
                    self.env.cr.commit()
            if  response_dict['cursor'] != None:
                spark_reading.cursor = response_dict['cursor']
                self.env.cr.commit()
                _logger.info("Trigger Next Cron")
                self.env.ref('mgs_sparkmeter.spark_cron')._trigger()
                return
            else:
                spark_reading.cursor = 'Done'
                self.env.cr.commit()

    @api.depends('progress','reading_ids', 'to_bill_count')
    def _compute_progress(self):
        for record in self:
            if record.to_bill_count > 0:
                record.progress = (record.reading_count / record.to_bill_count) * 100
            else:
                record.progress = 0

    @api.depends('date')
    def _compute_to_bill_count(self):
        property_obj = self.env['mgs_billing.property']
        for r in self:
            r.to_bill_count = property_obj.search_count(self._properties_domain())

    @api.depends('reading_ids')
    def _compute_reading_count(self):
        for r in self:
            r.reading_count = len(r.reading_ids.filtered(lambda x: x.state=='posted'))

    @api.depends('log_ids')
    def _compute_log_count(self):
        for r in self:
            r.log_count = len(r.log_ids.filtered(lambda x: x.state not in ('fail', 'posted') and x.eligible))
            r.fail_log_count = len(r.log_ids.filtered(lambda x: x.state == 'fail'))

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'mgs_sparkmeter.reading.seq') or '/'
        res = super(MgsSparkmeterReading, self).create(vals_list)
        res.message_subscribe(self.env.company.mgs_sparkmeter_follower_ids.partner_id.ids)
        return res
    
    def unlink(self):
        if len(self.reading_ids) > 0:
            raise UserError(
                "You cannot delete SparkMeter reading which has reading history.")
        return super(MgsSparkmeterReading, self).unlink()

    def action_open_readings(self):
        self.ensure_one()
        action = self.env.ref('mgs_billing.mgs_billing_reading_action').sudo().read()[0]
        action['domain'] = [('spark_reading_id', '=', self.id)]
        action['context'] = {}
        action['context']['create'] = False
        return action
    
    def action_open_log(self):
        self.ensure_one()
        action = self.env.ref('mgs_sparkmeter.mgs_sparkmeter_reading_log_action').sudo().read()[0]
        action['domain'] = [('spark_reading_id', '=', self.id),('state','!=','fail')]
        action['context'] = {'search_default_filter_eligible':1}
        return action

    def action_fail_open_log(self):
        self.ensure_one()
        action = self.env.ref('mgs_sparkmeter.mgs_sparkmeter_reading_log_action').sudo().read()[0]
        action['domain'] = [('spark_reading_id', '=', self.id),('state','=','fail')]
        action['context'] = {}
        return action


class MgsBillingReading(models.Model):
    _inherit = 'mgs_billing.reading'

    spark_reading_id = fields.Many2one('mgs_sparkmeter.reading',string='Spark Reading')
    spark_reading_log_id = fields.Many2one('mgs_sparkmeter.reading.log',string='Spark Reading Log')
    
    spark_current_reading = fields.Float()
    meter_type = fields.Selection([('normal', 'Normal'), ('smart', 'Smart')], compute="_compute_meter_type", store=True)
    
    @api.depends('property_id')
    def _compute_meter_type(self):
        for r in self:
            if r.property_id:
                r.meter_type = r.property_id.meter_type
            else:
                r.meter_type = None

    def action_sparkmeter_reading(self):
        for r in self:
            response = r.property_id._get_last_spark_reading()
            if response['code'] == 200:
                r.spark_current_reading = response['data']
            else:
                r.message_post(body="""Failed to fetch reading. Status code: """ + str(response['code'])+ """ Msg: """ + response['msg'])