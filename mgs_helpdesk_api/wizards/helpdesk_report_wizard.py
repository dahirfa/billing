from odoo import models, fields, api

class HelpdeskReportWizard(models.TransientModel):
    _name = 'helpdesk.report.wizard'
    _description = 'Helpdesk Report Wizard'

    date_from = fields.Date(string="Start Date", default=fields.Date.context_today)
    date_to = fields.Date(string="End Date", default=fields.Date.context_today)
    team_id = fields.Many2one('helpdesk.team', string="Team")
    user_id = fields.Many2one('res.users', string="Assigned User")
    zone_id = fields.Many2one('mgs_billing.zone', string="Zone")
    stage_id = fields.Many2one('helpdesk.stage', string="Stage")
    partner_id = fields.Many2one('res.partner', string="Customer")
    

    def print_report(self):
        datas = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'stage_id': self.stage_id.id if self.stage_id else False,
            'team_id': self.team_id.id if self.team_id else False,
            'team_name': self.team_id.name if self.team_id else False,
            'user_id': self.user_id.id if self.user_id else False,
            'user_name': self.user_id.name if self.user_id else False,
            'zone_id': self.zone_id.id if self.zone_id else False,
            'zone_name': self.zone_id.name if self.zone_id else False,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'partner_name': self.partner_id.name if self.partner_id else False,
        }
        return self.env.ref('mgs_helpdesk_api.action_report_helpdesk').report_action(self, data=datas)
