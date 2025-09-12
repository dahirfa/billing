# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = "res.company"

    mgs_billing_if_its_less_than = fields.Float(string="If it's less than")
    
    mgs_billing_make_rate = fields.Float(string="Make Rate")
    max_above_avg = fields.Float(string="Max Above Average")
    max_under_avg = fields.Float(string="Max Under Average")
    mgs_extra_service_ids = fields.Many2many(
        "product.product", string="Product", domain=[("type", "=", "service")]
    )
    mgs_billing_global_seq = fields.Boolean(
        default=False, string="Use a global sequence"
    )
    mgs_billing_global_seq_id = fields.Many2one("ir.sequence", string="Sequence")

    mgs_plan_categ_id = fields.Many2one("product.category", string="Plan Category")

    billing_period_start = fields.Integer(string="Billing Period (Start)")
    billing_period_end = fields.Integer(string="Billing Period (End)")

    
    
    is_allow_reg_date = fields.Boolean(string="Enable Allowed Registeration Date", default=False)
    
    allowed_reg_date = fields.Integer(string="Allowed Registeration Date")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mgs_billing_if_its_less_than = fields.Float(
        related="company_id.mgs_billing_if_its_less_than",
        readonly=False,
        string="If it's less than",
    )
    mgs_billing_make_rate = fields.Float(
        string="Make Rate", related="company_id.mgs_billing_make_rate", readonly=False
    )

    max_above_avg = fields.Float(
        string="Max Above Average", related="company_id.max_above_avg", readonly=False
    )
    max_under_avg = fields.Float(
        string="Max Under Average", related="company_id.max_under_avg", readonly=False
    )
    mgs_extra_service_ids = fields.Many2many(
        "product.product",
        string="Extra Services/Charges",
        related="company_id.mgs_extra_service_ids",
        readonly=False,
        domain=[("type", "=", "service")],
    )

    mgs_billing_global_seq = fields.Boolean(
        string="Use a global sequence",
        related="company_id.mgs_billing_global_seq",
        readonly=False,
    )

    mgs_billing_global_seq_id = fields.Many2one(
        "ir.sequence",
        string="Sequence",
        related="company_id.mgs_billing_global_seq_id",
        readonly=False,
    )

    billing_period_end = fields.Integer(
        string="Billing Period (Start)",
        related="company_id.billing_period_end",
        readonly=False,
    )
    billing_period_start = fields.Integer(
        string="Billing Period (Endd)",
        related="company_id.billing_period_start",
        readonly=False,
    )
    allowed_reg_date = fields.Integer(
        string="Allowed Registeration Date",
        related="company_id.allowed_reg_date",
        readonly=False,
    )

    
    is_allow_reg_date = fields.Boolean(string="Enable Allowed Registeration Date", default=False, related="company_id.is_allow_reg_date", readonly=False)


    mgs_plan_categ_id = fields.Many2one(
        "product.category",
        string="Plan Category",
        related="company_id.mgs_plan_categ_id",
        readonly=False,
    )
