from odoo import models, api
import logging
_logger = logging.getLogger(__name__)



class ReportTransfer(models.AbstractModel):
    _name = 'report.mgs_cash_transfer.report_transfer'
    _description = 'Transfer Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        
        domain = [('date', '>=', date_from),('date', '<=', date_to)]
        
        
        if data.get('journal_id'):
            domain.append(('journal_id', '=', data['journal_id']))      
            
        
        
        transfers = self.env['mgs_cash_transfer.transfer'].search(domain)

        return {
            'docs': transfers,
        }
