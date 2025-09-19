from odoo import models, fields, api
from odoo.exceptions import ValidationError
import xlsxwriter
import base64
from io import BytesIO
import logging
_logger = logging.getLogger(__name__)

class CallingReport(models.TransientModel):
    _name = 'mgs_billing.calling_report_wiz'
    _description = 'Calling Report'

    date_from = fields.Date(
        default=fields.Date.today().replace(day=1), required=True)
    date_to = fields.Date(default=fields.Date.today(), required=True)

    zone_id = fields.Many2one('mgs_billing.zone')
    collector_id = fields.Many2one('res.partner', string='Collector', domain=[('is_collector', '=', True)])
    states = fields.Selection(
        [('all', 'All'), ('posted', 'Posted')], default="posted", string='Target Moves', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    greater_less = fields.Selection(
        [('Greater', 'Greater than'), ('Less', 'Less than')], default="Greater", string='Show', required=True)
    greater_less_amount = fields.Float(
        string='Amount', default=1, required=True)
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    @api.constrains('date_from', 'date_to')
    def _check_the_date_from_and_to(self):
        if self.date_to and self.date_from and self.date_to < self.date_from:
            raise ValidationError('''From Date should be less than To Date.''')

    def confirm(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'zone_id': [self.zone_id.id, self.zone_id.name],
                'collector_id': [self.collector_id.id, self.collector_id.name],
                'states': self.states,
                'company_id': [self.company_id.id, self.company_id.name],
                'greater_less': self.greater_less,
                'greater_less_amount': self.greater_less_amount,
            },
        }
                
        _logger.info(data)
        return self.env.ref('mgs_billing.action_calling_report').report_action(self, data=data)
