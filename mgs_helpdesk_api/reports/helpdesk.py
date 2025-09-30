from odoo import models, api
import logging
_logger = logging.getLogger(__name__)



class ReportHelpdesk(models.AbstractModel):
    _name = 'report.mgs_helpdesk_api.report_helpdesk'
    _description = 'Helpdesk Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        
        domain = [('create_date', '>=', date_from),('create_date', '<=', date_to)]
        
        
        if data.get('team_id'):
            domain.append(('team_id', '=', data['team_id']))
        if data.get('user_id'):
            domain.append(('user_id', '=', data['user_id']))
        if data.get('zone_id'):
            domain.append(('partner_id.zone_id', '=', data['zone_id']))
        if data.get('partner_id'):
            domain.append(('partner_id', '=', data['partner_id']))        
        if data.get('stage_id'):
            domain.append(('stage_id', '=', data['stage_id']))        
            
        
        
        tickets = self.env['helpdesk.ticket'].search(domain)

        return {
            'docs': tickets,
            'team_name': data.get('team_name'),
            'user_name': data.get('user_name'),
            'zone_name': data.get('zone_name'),
            'partner_name': data.get('partner_name'),
        }
