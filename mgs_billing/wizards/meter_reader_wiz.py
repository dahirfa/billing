from odoo import models, fields, api

class MeterReaderSummaryWizard(models.TransientModel):
    _name = 'mgs_billing.meter.reader.summary.wizard'
    _description = 'Meter Reader Summary Wizard'

    collector_id = fields.Many2one(
        'res.partner', 
        string="Meter Reader",
        domain=[('is_collector','=',True)]
        
    )
    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.today
        
    )

    def action_print_report(self):
        self.ensure_one()
        data = {
            'collector_id': self.collector_id.id,
            'date': self.date,
            
        }
        return self.env.ref('mgs_billing.action_meter_reader_summary').report_action(self, data=data)
