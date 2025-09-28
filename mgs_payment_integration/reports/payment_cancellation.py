from odoo import models, fields, api
class PaymentCancellationReport(models.AbstractModel):
    _name = 'report.mgs_payment_integration.report_payment_cancellation'
    _description = 'Payment Cancellation Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        partner_id = data.get('partner_id')

        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('state', '=', 'canceled'), 
        ]
        if partner_id:
            domain.append(('partner_id', '=', partner_id))

        payments = self.env['account.payment'].search(domain)

        return {
            'docs': payments,
            'date_from': date_from,
            'date_to': date_to,
            'partner': self.env['res.partner'].browse(partner_id) if partner_id else False,
        }

