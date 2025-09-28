from odoo import models, api

class ReportHelpdesk(models.AbstractModel):
    _name = 'report.mgs_helpdesk_api.report_helpdesk'
    _description = 'Helpdesk Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('team_id'):
            domain.append(('team_id', '=', data['team_id']))
        if data.get('user_id'):
            domain.append(('user_id', '=', data['user_id']))
        if data.get('zone_id'):
            domain.append(('partner_id.zone_id', '=', data['zone_id']))
        if data.get('partner_id'):
            domain.append(('partner_id', '=', data['partner_id']))

        tickets = self.env['helpdesk.ticket'].search(domain)

        return {
            'docs': tickets,
        }
