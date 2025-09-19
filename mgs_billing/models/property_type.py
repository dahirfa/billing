from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class MGSBillingPropertyType(models.Model):
    _name = "mgs_billing.property.type"
    _description = "MGS Billing Document Type"
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id DESC"

    name = fields.Char("Name", required=True)
  
    property_ids = fields.One2many(
        "mgs_billing.property", "property_type_id", string="Properties"
    )
    counter = fields.Integer(string="Properties", compute="_count_properties")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company.id
    )

    max_above_avg = fields.Float(string="Max Above Average")
    max_under_avg = fields.Float(string="Max Under Average")

    custom_average = fields.Boolean(default=False, string="Use Custom Average")
    if_its_less_than = fields.Float(string="If it's less than")
    make_rate = fields.Float(string="Make Amount")

    product_id = fields.Many2one(
        "product.product", string="Billing Plan", domain=[("is_billing_pan", "=", True)]
    )

    @api.depends("property_ids")
    def _count_properties(self):
        for r in self:
            r.counter = len(r.property_ids.ids)

    def action_open_properties(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Properties",
            "view_mode": "list,form",
            "res_model": "mgs_billing.property",
            "domain": [("property_type_id", "=", self.id)],
            "context": "{'create': False}",
        }

    def unlink(self):
        property_ids = self.env["mgs_billing.property"].search(
            [("property_type_id", "=", self.id)]
        )

        if len(property_ids) > 0:
            raise UserError(
                "You cannot delete property type which has related properties."
            )
        return super(MGSBillingPropertyType, self).unlink()
