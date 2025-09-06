from datetime import datetime, timedelta, date
from odoo import models, fields, api


class PrintOpportunity(models.TransientModel):
    _name = 'crm_extension.print_opportunity'
    _description = 'Print Opportunity'

    date = fields.Date()
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company.id, required=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', required=True)

    def confirm(self):
        """Call when button 'Get Rep=t' clicked.
        """

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date': self.date,
                'company_id': self.company_id.id,
                'company_name': self.company_id.name,
                'stage_id': self.stage_id.id,
                'stage_name': self.stage_id.name
            },
        }

        return self.env.ref('crm_extension.action_print_opportunity').report_action(self, data=data)


class PrintOpportunityReport(models.AbstractModel):
    _name = 'report.crm_extension.print_opportunity_report'
    _description = 'Print Opportunity Report'

    @api.model
    def _lines(self, date, stage_id, company_id):
        from_date = str(date) + " 00:00:00"
        to_date = str(date) + " 23:59:59"

        params = [stage_id, company_id]
        # select rp.name as partner_name, rp.mobile as mobile, rp.phone as phone, zone.name as zone_id
        # left join res_partner as rp on cl.partner_id=rp.id
        # left join mgs_billing_zone as zone on rp.zone_id=zone.id
        query = """
            select cl.name, cl.phone, cl.street
            from crm_lead as cl
            where cl.stage_id=%s
            and cl.company_id=%s
        """

        if date:
            query += " and cl.create_date >= '%s'" % from_date

            query += " and cl.create_date <= '%s'" % to_date

        query += " order by cl.create_date"

        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        return res

    @api.model
    # def _get_report_values(self, docids, data=None):
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        date = data['form']['date']
        company_id = data['form']['company_id']
        company_name = data['form']['company_name']
        stage_id = data['form']['stage_id']
        stage_name = data['form']['stage_name']

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'date': date,
            'stage_id': stage_id,
            'stage_name': stage_name,
            'company_id': self.env['res.company'].search([('id', '=', company_id)]),
            'company_name': company_name,
            'lines': self._lines
        }
