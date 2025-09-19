# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    zone_id = fields.Many2one(
        'mgs_billing.zone', string='Zone', tracking=True)

    property_id = fields.Many2one(
        'mgs_billing.property', string='Property', tracking=True)

    owner_id = fields.Many2one(
        'mgs_billing.partner', string='Owner', tracking=True)

    billing_account_id = fields.Many2one(
        'res.partner', string='Billing Account', tracking=True)
    
    property_type_id = fields.Many2one('mgs_billing.property.type', string='Property Type', ondelete='restrict', tracking=True)
    
    
    mobile = fields.Char(string="Tenant's Mobile")
    
    
    pipe_extention = fields.Char(string='pipe extention')
    pipe_type = fields.Char(string='Pipe Type')
    meter_category = fields.Char(string='Meter Category')
    
    
    
    
    
    hide_create_customer_btn = fields.Boolean(
        default=False, compute='_compute_hide_create_customer_btn')
    
    help_desk_ticket_id = fields.Many2one(
        'helpdesk.ticket', string='Ticket', index=True)
    
    
    hide_create_ticket_btn = fields.Boolean(
        default=False, compute='_compute_hide_create_ticket_btn')
    


    @api.depends('partner_id', 'property_id')
    def _compute_hide_create_customer_btn(self):
        for r in self:
            r.hide_create_customer_btn = False
            if r.partner_id and r.property_id:
                r.hide_create_customer_btn = True

    @api.depends('help_desk_ticket_id')
    def _compute_hide_create_ticket_btn(self):
        for r in self:
            r.hide_create_ticket_btn = False
            if r.help_desk_ticket_id.id:
                r.hide_create_ticket_btn = True

    def create_helpdesk_ticket(self):
        for r in self:
            if not r.help_desk_ticket_id:
                vals = {
                    'name': r.name,
                    'partner_name': r.name,
                    'street': r.street,
                    'zone_id': r.zone_id.id,
                    'partner_phone': r.phone,
                    'crm_lead_id': r.id,
                    'partner_id': r.partner_id.id
                }

                created_ticket = self.env['helpdesk.ticket'].create(vals)

                r.help_desk_ticket_id = created_ticket.id


    def action_open_ticket(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ticket',
            'view_mode': 'list,form',
            'res_model': 'helpdesk.ticket',
            'domain': [('crm_lead_id', '=', self.id)],
            'context': "{'create': False}"}


class HelpdesTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    crm_lead_id = fields.Many2one(
        'crm.lead', string='CRM Lead', index=True)
