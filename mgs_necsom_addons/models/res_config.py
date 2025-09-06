# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    mgs_auto_reconnect_house = fields.Boolean(
        default=False, string='Auto Reconnect')
    mgs_reconnection_percentage = fields.Float(
        string="Reconnection Percentage")

    mgs_tax_account_ids = fields.Many2many(
        'account.account', string="Tax Report Accounts")

    mgs_tax_account_ids = fields.Many2many(
        'account.account', string="Tax Report Accounts")

    next_crm_stage_id = fields.Many2one('crm.stage', string="Next Stage ")
    # ticket_type_id = fields.Many2one(
    #     'helpdesk.ticket.type', string="Default Ticket Type ")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mgs_auto_reconnect_house = fields.Boolean(
        string='Auto Reconnect', related="company_id.mgs_auto_reconnect_house", readonly=False)
    mgs_reconnection_percentage = fields.Float(
        related="company_id.mgs_reconnection_percentage", readonly=False, string="Reconnection Percentage")
    mgs_tax_account_ids = fields.Many2many(
        'account.account', string="Tax Report Accounts", related="company_id.mgs_tax_account_ids", readonly=False)

    next_crm_stage_id = fields.Many2one(
        'crm.stage', string="Next Stage ", related="company_id.next_crm_stage_id", readonly=False)
    # ticket_type_id = fields.Many2one(
    #     'helpdesk.ticket.type', string="Default Ticket Type ", related="company_id.ticket_type_id", readonly=False)
