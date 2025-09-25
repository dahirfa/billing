from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class Mgs_Create_Ticket(models.TransientModel):
    _name = 'mgs.create.ticket.wizard'
    _description = 'Create Ticket Wizard'

    title = fields.Char(string="Title")
    partner_id = fields.Many2one('res.partner', index=True, string="Partner")
    team_id = fields.Many2one('helpdesk.team', string="Helpdesk Team", readonly=False, default=lambda self: self.env.company.team_id.id)
    tag_id = fields.Many2one('helpdesk.tag', string="Helpdesk Tag", readonly=False, default=lambda self: self.env.company.tag_id.id)
    

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')

        if active_model == 'crm.lead' and active_ids:
            lead = self.env[active_model].browse(active_ids[0])
            res.update({
                'partner_id': lead.partner_id.id,
            })
        return res

    def action_confirm(self):        
        
        for r in self:                
            context = dict(self._context or {})
            active_model = context.get('active_model')
            active_ids = context.get('active_ids')

            if active_model == 'crm.lead' and active_ids:
                lead = self.env[active_model].browse(active_ids[0])
            if not lead.help_desk_ticket_id:
                
                vals = {
                    "name": r.title,
                    "partner_name": r.partner_id.name,
                    "street": lead.street,
                    "zone_id": lead.zone_id.id,
                    "partner_phone": lead.phone,
                    "crm_lead_id": lead.id,
                    "team_id": r.team_id.id,
                    'tag_ids': [(4, r.tag_id.id)],
                    "partner_id": r.partner_id.id,
                }

                created_ticket = self.env["helpdesk.ticket"].create(vals)

                lead.help_desk_ticket_id = created_ticket.id        
        
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': f"Ticket {created_ticket.name} has been created successfully.",
                        'type': 'success',
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }




