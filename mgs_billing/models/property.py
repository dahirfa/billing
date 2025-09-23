from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


# from statistics import mean
# from odoo.exceptions import UserError


class MGSBillingPropertyConHistory(models.Model):
    _name = "mgs_billing.property.connection.log"
    _description = "Connection History"
    _order = "time DESC"

    property_id = fields.Many2one("mgs_billing.property")
    time = fields.Datetime(default=fields.Datetime().now())
    memo = fields.Text(string="Comment")
    state = fields.Selection(
        [("connected", "Connected"), ("disconnected", "disconnected")]
    )



class MGSBillingProperty(models.Model):
    _name = "mgs_billing.property"
    _description = "Billing Property"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id DESC"

    name = fields.Char(string="House #", default="/", tracking=True)
    
    billing_account_id = fields.Many2one(
        string='Billing Account',
        comodel_name='res.partner',
        ondelete='restrict',
    )
    
    property_type_id = fields.Many2one(
        "mgs_billing.property.type",
        string="Property Type",
        ondelete="restrict",
        tracking=True,
    )
    zone_id = fields.Many2one(
        "mgs_billing.zone",
        string="Zone",
        ondelete="restrict",
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company.id
    )
    city = fields.Char(tracking=True)
    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)
    zip = fields.Char()
    country_id = fields.Many2one(
        "res.country", string="Country", ondelete="restrict", tracking=True
    )
    state_id = fields.Many2one(
        "res.country.state", string="Country", ondelete="restrict"
    )
  
    billing_customer_id = fields.Many2one(
        "mgs_billing.billing_customer",
        tracking=True,
        required=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Plan",
        domain=[("is_billing_pan", "=", True)],
        required=True,
        tracking=True,
    )
    reading_history_counter = fields.Integer(
        string="Reading History", compute="get_reading_history"
    )
    meter_reading_ids = fields.One2many("mgs_billing.meter.reading", "property_id")
    connection_log_ids = fields.One2many(
        "mgs_billing.property.connection.log", "property_id"
    )
    connection_log_count = fields.Integer(
        "Log Count", default=0, compute="_compute_connection_log_count", store=True
    )
    
    meter_id = fields.Many2one("mgs_billing.meter", ondelete="restrict")
    
    initial_meter = fields.Float(string="Initial Meter Read", tracking=True)


    meter_type = fields.Selection(
        [("normal", "Normal"), ("smart", "Smart")], default="normal", required=True
    )

    state = fields.Selection(
        [("connected", "Connected"), ("disconnected", "Disconnected")],
        default="connected",
        tracking=True,
    )
    
    customer_type = fields.Selection([('normal', 'Normal Customer'), ('free', 'Free Customer')], string='Customer Type', defualt="normal")
    
    exclude_tax = fields.Boolean(string='Exclude Tax')
    
    suspended = fields.Boolean(default=False, tracking=True)
    suspension_date = fields.Date(tracking=True)
    connection_date = fields.Datetime(string="Connection Date", tracking=True)

    def action_unsuspend(self):
        for r in self:
            r.suspended = False
            self.action_change_state("connected")


    @api.depends("connection_log_ids")
    def _compute_connection_log_count(self):
        for r in self:
            r.connection_log_count = len(r.connection_log_ids)

    def action_change_state(self, state="", memo=""):
        log_obj = self.env["mgs_billing.property.connection.log"]
        state = state
        for r in self.filtered(lambda x: x.state != state):
            r.state = state
            log_obj.create(
                {
                    "property_id": r.id,
                    "state": state,
                    "memo": memo,
                }
            )

    def action_connected(self):
        self.action_change_state("connected")

    def action_disconnected(self, wizard=False):
        if wizard != True:
            self.action_change_state("disconnected")

    def action_open_conncection_log(self):
        action = (
            self.env.ref("mgs_billing.mgs_billing_connection_log_action")
            .sudo()
            .read()[0]
        )
        action["domain"] = [("property_id", "=", self.id)]
        action["context"] = {}
        action["context"]["create"] = False
        return action

    # @api.model
    def write(self, vals):
        if vals.get("zone_id"):
            if not self.env.company.mgs_billing_global_seq:
                if vals.get("name") and vals.get("name") != "/":
                    pass
                else:
                    vals["name"] = (self.env["ir.sequence"].next_by_code(self.env["mgs_billing.zone"]
                            .search([("id", "=", vals.get("zone_id"))])
                            .code
                        )
                        or "/"
                    )


        if vals.get("billing_customer_id"):
            partner = self.env["res.partner"].search([("is_tenancy", "=", True), ("property_id.id", "=", self.id)], limit=1)
            partner.billing_customer_id = vals.get("billing_customer_id")
            partner._compute_billing_name()
            partner._onchange_billing_name()

        return super(MGSBillingProperty, self).write(vals)

    def unlink(self):
        reading_ids = self.env["mgs_billing.reading"].search_count(
            [("property_id", "=", self.id)]
        )
        if reading_ids:
            raise UserError("You cannot delete property which has reading history.")
        return super(MGSBillingProperty, self).unlink()

    @api.model_create_multi
    def create(self, vals_list):

        recs = super(MGSBillingProperty, self).create(vals_list)

        for res in recs:

            if not self.env.company.mgs_billing_global_seq:
                if res["name"] and res["name"] != "/":
                    continue
                res["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        self.env["mgs_billing.zone"]
                        .search([("id", "=", res.zone_id.id)])
                        .code
                    )
                    or "/"
                )
            else:
                mgs_billing_global_seq_id = self.env.company.mgs_billing_global_seq_id
                if not mgs_billing_global_seq_id:
                    raise UserError(
                        "Please select default global sequence in the billing settings"
                    )
                res["name"] = (
                    self.env["ir.sequence"].next_by_code(mgs_billing_global_seq_id.code)
                    or "/"
                )

        return recs
    
    
    
    def create_billing_account(self, partner_id=False):
        Partner = self.env["res.partner"]

        for rec in self:
            # CASE 1: Create billing account if none exists and no partner_id provided
            if not rec.billing_account_id and not partner_id:
                vals = {
                    "name": " - ".join((rec.billing_customer_id.name, rec.name)),
                    "is_tenancy": True,
                    "property_id": rec.id,
                    "product_id": rec.product_id.id,
                    "billing_customer_id": rec.billing_customer_id.id,
                    "mobile": rec.billing_customer_id.mobile,
                    "phone": rec.billing_customer_id.phone,
                    "email": rec.billing_customer_id.email,
                    "image_1920": rec.billing_customer_id.image,
                    "street": rec.street,
                    "street2": rec.street2,
                    "city": rec.city,
                    "country_id": rec.country_id.id if rec.country_id else False,
                    "state_id": rec.state_id.id if rec.state_id else False,
                    "zip": rec.zip,
                    "category_id": [(4, rec.zone_id.partner_category_id.id)] if rec.zone_id.partner_category_id else [],
                }
                created_billing_account = Partner.create(vals)


                rec.billing_account_id = created_billing_account.id

            elif partner_id:
                partner = Partner.browse(partner_id)
                if partner and not partner.property_id:
                    partner_vals = {
                        "name": " - ".join((rec.billing_customer_id.name, rec.name)),
                        "is_tenancy": True,
                        "property_id": rec.id,
                        "product_id": rec.product_id.id,
                        "billing_customer_id": rec.billing_customer_id.id,
                        "mobile": rec.billing_customer_id.mobile,
                        "phone": rec.billing_customer_id.phone,
                        "email": rec.billing_customer_id.email,
                        "image_1920": rec.billing_customer_id.image,
                        "street": rec.street,
                        "street2": rec.street2,
                        "city": rec.city,
                        "country_id": rec.country_id.id if rec.country_id else False,
                        "state_id": rec.state_id.id if rec.state_id else False,
                        "zip": rec.zip,
                        "category_id": [(4, rec.zone_id.partner_category_id.id)] if rec.zone_id.partner_category_id else [],
                    }
                    partner.write(partner_vals)
                    rec.billing_account_id = partner.id



    def get_reading_history(self):
        for r in self:
            r.reading_history_counter = self.env['mgs_billing.meter.reading'].search_count([('property_id.id', '=', r.id)])

    def action_open_reading_history(self):

        return {
            'name': 'Reading History',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'mgs_billing.meter.reading',
            "context": {"create": False},
            'domain': [('property_id.id', '=', self.id)],
        }
    








