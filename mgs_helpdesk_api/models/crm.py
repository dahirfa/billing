# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Mgs_Crm_Extension(models.Model):
    _inherit = "crm.lead"    

    help_desk_ticket_id = fields.Many2one(
        "helpdesk.ticket", string="Ticket", index=True
    )

    hide_create_ticket_btn = fields.Boolean(
        default=False, compute="_compute_hide_create_ticket_btn"
    )

    @api.depends("help_desk_ticket_id")
    def _compute_hide_create_ticket_btn(self):
        for r in self:
            r.hide_create_ticket_btn = False
            if r.help_desk_ticket_id.id:
                r.hide_create_ticket_btn = True


    def action_open_ticket(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Ticket",
            "view_mode": "list,form",
            "res_model": "helpdesk.ticket",
            "domain": [("crm_lead_id", "=", self.id)],
            "context": "{'create': False}",
        }

