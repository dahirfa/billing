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
        ...
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': 'Success',
        #         'message': f"Meter '{self.meter_id.name}' has been successfully assigned to property '{self.property_id.name}'.",
        #         'type': 'success',
        #         'sticky': False,
        #         'next': {'type': 'ir.actions.act_window_close'},
        #     }
        # }




