
# -*- coding: utf-8 -*-
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


class MgsBillingMove(models.Model):
    _inherit = 'account.move'

    mgs_auto_tax_id = fields.Many2one('mgs.tax.auto.invoice',string='Mgs Auto Tax')
    
    
class MgsSparkmeterAutoTax(models.Model):
    _name = 'mgs.tax.auto.invoice'
    _description = 'Auto Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id DESC"

    name            = fields.Char(string='Ref', copy=False, default='/', readonly=True)
    date            = fields.Date(default=fields.Date.today(), required=True, tracking=1, readonly=True)
    invoice_ids     = fields.One2many('account.move', 'mgs_auto_tax_id', copy=False)
    invoice_count   = fields.Integer(string='No of Inovices', default=0, compute='_compute_invoice_count')
    to_bill_count   = fields.Integer(compute='_compute_to_bill_count', string="To Bill", store=True, copy=False)
    progress        = fields.Float(compute='_compute_progress', store=True, copy=False)
    state           = fields.Selection([('queue','In Queue'),('done', 'Done')], default='queue')
    property_ids    = fields.Many2many('mgs_billing.property')

    
    def action_trigger_cron(self):
        invoice_obj = self.env['account.move']
        partner_obj = self.env['res.partner']
        
        for rec in self:
            if not rec.property_ids:
                raise ValidationError("No properties to invoice")
            
          
            property_ids_list = rec.property_ids.ids
                   
            batch_size = 50
            for i in range(0, len(property_ids_list), batch_size):
                batch_property_ids = property_ids_list[i:i + batch_size]
                
                for property_id in batch_property_ids:
                    try:
                        partner_id = partner_obj.search([('property_id.id', '=', property_id)], limit=1)
                        invoice = invoice_obj.create(rec._prepare_invoice(partner_id))
                        invoice.action_post()
                    except Exception as e:
                        self.env.cr.rollback()
                        rec.message_post(body=f"Failed to create Invoice for Property ID {property_id}: {e}")
                        self.env.cr.commit()
                    else:
                        rec.property_ids = [(3, property_id, 0)]
                        self.env.cr.commit()
        
        
    def _properties_domain(self):
        domain = [('meter_type','=','smart'), ('payment_type','=','pre_paid'), ('state','=','connected')]
        return domain

    @api.model
    def action_auto_invoice_hd_taxes(self, batch_size=50):
        current_date            = date.today()
        company                 = self.env.company
        auto_tax_record         = self.search([('date','=',current_date)], limit=1)
        if not auto_tax_record:
            auto_tax_record=self.create({'date':current_date})

        properties              = auto_tax_record.property_ids[:batch_size + 1]
        next_cron_trigger       = False
        
        if len(properties) > 50:
            next_cron_trigger   = True
            

        invoice_obj = self.env['account.move']
        partner_obj = self.env['res.partner']
        
        for record in properties:
            try:
                partner_id  = partner_obj.search([('property_id','=',record.id)],limit=1)
                invoice     = invoice_obj.create(auto_tax_record._prepare_invoice(partner_id))
                invoice.action_post()
            except Exception as e:
                self.env.cr.rollback()
                auto_tax_record.message_post(body=f"Failed to create Invoice for Property {record.name} : {e}")
                self.env.cr.commit()
            else:
                auto_tax_record.property_ids = [(3, record.id, 0)]
                self.env.cr.commit()
        if  next_cron_trigger:
            _logger.info("Trigger Next H/D Auto Invoice Cron")
            self.env.ref('mgs_billing_prepayment.mgs_auto_invoice_tax_cron')._trigger()
            return
        else:
            auto_tax_record.state = 'done'
            self.env.cr.commit()

    def _prepare_invoice(self, partner_id):
        lines   = [[0,0, {'product_id': service.id}] for service in self.env.company.mgs_extra_service_ids]
        move    = {
            'move_type'         : 'out_invoice',
            'invoice_date'      : self.date,
            'partner_id'        : partner_id.id,
            'invoice_origin'    : self.name,
            'mgs_auto_tax_id'   : self.id,
            'invoice_line_ids'  : lines
            }
        return move
    
    @api.depends('progress','invoice_ids', 'to_bill_count')
    def _compute_progress(self):
        for record in self:
            if record.to_bill_count > 0:
                record.progress = (record.invoice_count / record.to_bill_count) * 100
            else:
                record.progress = 0

    @api.depends('date')
    def _compute_to_bill_count(self):
        property_obj = self.env['mgs_billing.property']
        for r in self:
            r.to_bill_count = property_obj.search_count(self._properties_domain())

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for r in self:
            r.invoice_count = len(r.invoice_ids)

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('mgs.tax.auto.invoice.seq') or '/'
        res = super(MgsSparkmeterAutoTax, self).create(vals_list)
        property_ids = self.env['mgs_billing.property'].search(self._properties_domain()).ids
        res.property_ids = [(6,0,property_ids)]
        return res
    
    def unlink(self):
        if len(self.invoice_ids) > 0:
            raise UserError(
                "You cannot delete a record that has attached invoices.")
        return super(MgsSparkmeterAutoTax, self).unlink()

    def action_open_invoices(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type').sudo().read()[0]
        action['domain'] = [('mgs_auto_tax_id', '=', self.id)]
        action['context'] = {}
        action['context']['create'] = False
        return action
