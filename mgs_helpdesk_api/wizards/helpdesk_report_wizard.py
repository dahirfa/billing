from odoo import models, fields, api

class HelpdeskReportWizard(models.TransientModel):
    _name = 'helpdesk.report.wizard'
    _description = 'Helpdesk Report Wizard'

    team_id = fields.Many2one('helpdesk.team', string="Team")
    user_id = fields.Many2one('res.users', string="Assigned User")
    zone_id = fields.Many2one('mgs_billing.zone', string="Zone")
    partner_id = fields.Many2one('res.partner', string="Customer")

    def print_report(self):
        datas = {
            'team_id': self.team_id.id if self.team_id else False,
            'user_id': self.user_id.id if self.user_id else False,
            'zone_id': self.zone_id.id if self.zone_id else False,
            'partner_id': self.partner_id.id if self.partner_id else False,
        }
        return self.env.ref('mgs_helpdesk_api.action_report_helpdesk').report_action(self, data=datas)
