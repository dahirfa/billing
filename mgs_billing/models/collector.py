from odoo import models, fields, api
from odoo.exceptions import ValidationError
from lxml import etree
from odoo.tools.safe_eval import safe_eval

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"
    
    # TODO MAKE DYNAMIC FIELD NAME WORK!!!!
    # @api.model
    # def _get_view(self, view_id=None, view_type="form", **options):
    #     arch, view = super()._get_view(view_id, view_type, **options)
    #     action = self.env.ref("mgs_billing.mgs_billing_collector_action")
    #     ctx_str = action.context        # this is a string
    #     ctx = safe_eval(ctx_str) if ctx_str else {}
        
    #     _logger.info(ctx['default_is_collector'])
    #     if view_type == "form" and ctx['default_is_collector']:
    #         for node in arch.xpath("//field[@name='mobile']"):
    #             node.set("string", "Collector's Mobile")
    #         for node in arch.xpath("//field[@name='phone']"):
    #             node.set("string", "Collector's Phone")


    #     return arch, view

    # @api.model
    #    def _get_view(self, view_id=None, view_type='form', **options):
    #        arch, view  = super()._get_view(view_id, view_type, **options)
    #        active_company = self.env.company
    #        if view_type == 'form' and active_company.name == 'My Company B':
    #            for node in arch.xpath("//field[@name='origin']"):
    #                node.set('string', 'Doc Number')
    #        if view_type == 'form' and active_company.name == 'My Company A':
    #            for node in arch.xpath("//field[@name='origin']"):
    #                node.set('string', 'Order Reference')
    #        return arch, view

    # if self._context.get('default_is_collector'):
    #     for node in doc.xpath("//field[@name='mobile']"):
    #         node.set('string', "Collector's Mobile")
    #     for node in doc.xpath("//field[@name='phone']"):
    #         node.set('string', "Collector's Phone")

    is_collector = fields.Boolean(default=False)

    assigned_zone_ids = fields.Many2many(
        string="Assigned Zone",
        comodel_name="mgs_billing.zone",
        compute="_compute_assigned_zone_id",
        ondelete="restrict",
    )

    @api.depends("assigned_zone_ids")
    def _compute_assigned_zone_id(self):
        for record in self:
            record.assigned_zone_ids = (
                self.env["mgs_billing.zone"]
                .search([("collector_id.id", "=", record.id)])
                .ids
            )
