from odoo import models, fields, api, tools
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError


class MgsRecivablesReport(models.TransientModel):
    _name = 'mgs_billing.connect_disconnect.wizard'
    _description = 'mgs_billing.connect_disconnect.wizard'

    zone_id = fields.Many2one('mgs_billing.zone', required=False)
    # collector_id = fields.Many2one(
    #     'res.partner', string='Collector', domain=[('is_collector', '=', True)])
    collector_ids = fields.Many2many('res.partner', string='Collectors', domain=[('is_collector', '=', True)], tracking=True)
    state = fields.Selection(
        [('connected', 'Connected'), ('disconnected', 'Disconnected')], default='disconnected', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)

    def action_view_report(self):
        report_obj = self.env['mgs_billing.connect_disconnect.report']

        query = report_obj.query_execute(
            self.state, self.zone_id.id, self.collector_ids.ids, self.company_id.id)

        tools.drop_view_if_exists(self._cr, report_obj._table)
        self._cr.execute('''CREATE OR REPLACE VIEW %s AS (%s)''' %
                         (report_obj._table, query))
        action = self.env.ref(
            'mgs_billing.mgs_billing_connect_disconnect_report_action').sudo().read()[0]
        action['context'] = {}
        action['context']['create'] = False
        return action
