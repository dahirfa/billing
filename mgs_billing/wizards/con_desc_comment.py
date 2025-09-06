from odoo import models, fields, api, tools
from odoo.exceptions import UserError, AccessError


class ConnDescCommentWiz(models.TransientModel):
    _name = 'mgs_billing.con_desc_comment.wizard'
    _description = 'Connect/disconnect Comment Wizard'

    property_id = fields.Many2one(
        'mgs_billing.property', index=True, string="Property")

    memo = fields.Text(string='Comment', required=True)

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)

    state = fields.Selection(
        [('connected', 'Connected'), ('disconnected', 'Disconnected')])

    @api.model
    def default_get(self, fields):
        rec = super(ConnDescCommentWiz, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        property_id = self.env[active_model].browse(active_ids)

        rec.update({
            'property_id': property_id.id,
        })
        return rec

    def action_confirm(self):
        if self.state == 'connected':
            self.property_id.action_change_state('connected', self.memo)
        else:
            self.property_id.action_change_state('disconnected', self.memo)
