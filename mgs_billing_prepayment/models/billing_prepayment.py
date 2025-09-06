from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import requests
import json
import logging
_logger = logging.getLogger(__name__)



class AccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    spark_eligible          = fields.Boolean(compute="_compute_spark_eligible", store=True, default=False, copy=False)
    spark_pid               = fields.Char(tracking=True, copy=False)
    prepaid_electricity     = fields.Boolean(string="Prepaid Electricity", default=False)
    property_payment_type   = fields.Selection(string="Payment Type",related="partner_id.property_id.payment_type",)
    

    @api.depends('partner_id')
    def _compute_spark_eligible(self):
        for r in self:
            r.spark_eligible = False
            if r.partner_id.property_id.property_sparkmeter_customer_id:
                r.spark_eligible = True


    def action_draft(self):
        try:
            _logger.info("--------Sparkmeter Payment Reversal--------------")
            self.filtered(lambda x: x.spark_pid != False and x.spark_eligible).action_reverse_spark_payment()
        except Exception as e:
            _logger.error("--------Failed Sparkmeter Payment Reversal--------------")
            _logger.info(e)
            raise UserError(e)
        return super(AccountPaymentInherit, self).action_draft()


    def action_post(self):
        res = super(AccountPaymentInherit, self).action_post()
        for r in self:
            if r.spark_eligible and r.prepaid_electricity:
                _logger.info("--------Create Sparkmeter Payment--------------")
                try:
                    r._prepare_request()
                except Exception as e:
                    _logger.error("--------Failed To Create Sparkmeter Payment--------------")
                    _logger.info(e)
                    raise UserError(e)
        return res
    
    
    def _prepare_headers(self):
        current_company = self.env.company
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": current_company.mgs_sparkmeter_api_key,
            "X-API-SECRET": current_company.mgs_sparkmeter_api_secret
            }
        return headers
    
    def _prepare_request(self):
        if not self.spark_eligible:
            raise UserError("This customer is not registered in sparkmeter.")
        if self.state!='posted':
            raise UserError("Payment is not posted.")
        current_company = self.env.company
        payload={
            "amount": str(self.amount),
            "memo": self.ref or self.name,
            "external_id": self.name
            }
        _logger.info(payload)
        url = '%s/customers/%s/payments' % (current_company.mgs_sparkmeter_api_link, self.partner_id.property_id.property_sparkmeter_customer_id)
        response = requests.post(url, headers=self._prepare_headers(), json=payload)
        response_dict = json.loads(response.text)
        _logger.info(response_dict)
        if response_dict['data'] and response_dict['data'] and response.status_code == 201:
            self.message_post(body="Spark : Payment created successfully. Status code: " + str(response.status_code))
            self.spark_pid = response_dict['data']['id']
        else:
            self.message_post(body="""Spark : Failed to create payment. Status code: """ + str(response.status_code))

    def action_reverse_spark_payment(self):
        for r in self:
            url = '%s/payments/%s/reverse' % (self.env.company.mgs_sparkmeter_api_link, r.spark_pid)
            response = requests.post(url, headers=r._prepare_headers())
            response_dict = json.loads(response.text)
            _logger.info(response_dict)
            if response.status_code == 201:
                self.message_post(body="Spark : Payment reversed successfully. Status code: " + str(response.status_code))
            else:
                self.message_post(body="""Spark : Failed to reverse payment. Status code: """ + str(response.status_code))

    
    def action_create_spark_payment(self):
        for r in self.filtered(lambda x: x.partner_id.property_id.meter_type == 'smart'):
            r._prepare_request()

class MGSProperty(models.Model):
    _inherit = "mgs_billing.property"

    payment_type = fields.Selection(
        string="Payment Type",
        selection=[("pre_paid", "Prepaid"), ("post_paid", "Postpaid")],
        default="post_paid",
        required=True,
        tracking=True,
    )
    
    @api.onchange('payment_type')
    def onchange_payment_type(self):
        for rec in self:
            if rec.payment_type == 'pre_paid' and (rec.get_partner_balance(rec._origin.id) > 0 or rec.get_partner_balance(rec._origin.id) < 0):
                raise UserError(f"Property Has Pending Balance of: {rec.get_partner_balance(rec._origin.id)}") 
    
    
    def get_partner_balance(self, property_id):
        partner_id = self.env['res.partner'].search([('property_id.id', '=', property_id)], limit=1).id
        partner_balance = """
                            select COALESCE(sum(aml.debit - aml.credit), 0)
                            from account_move_line as aml
                            left join account_account as aa on aml.account_id=aa.id
                            where aml.partner_id = %s""" % str(partner_id) + """
                            and aa.account_type = 'asset_receivable'
                            and parent_state in ('posted')"""
        self.env.cr.execute(partner_balance)
        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result    




class MgsBillingReading(models.Model):
    _inherit = 'mgs_billing.reading'
    
    def _prepare_invoice_data(self, start_date, end_date):
        action = super(MgsBillingReading, self)._prepare_invoice_data(start_date, end_date)
        partner_id = self.billing_account_id
        if partner_id.property_id.payment_type == "pre_paid":
            action['move_type'] = 'in_refund'
        _logger.info(action)
        return action
    
    
    def _prepare_invoice_line(self, service_ids):
        action = super(MgsBillingReading, self)._prepare_invoice_line(service_ids)        
        
        if self.billing_account_id.property_id.payment_type == "pre_paid":
            if action and len(action) > 0:
                first_item = list(action[0]) 
                first_item[2]['tax_ids'] = False # [(0, 0, {})]
                action[0] = tuple(first_item)
                
                # Remove the second item from the action list
                if len(action) > 1:
                    action.pop(1)
        
        return action
    