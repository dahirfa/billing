from odoo import models

import logging
_logger = logging.getLogger(__name__)


class HrExpenseReport(models.AbstractModel):
    _name = 'report.mgs_expense_report.hr_expense_report_template'
    _description = 'HR Expense Report'

    def _get_report_lines(self, data):
        domain = [
            ('date', '>=', data['date_from']),
            ('date', '<=', data['date_to']),
        ]
        if data.get('product_id'):
            domain.append(('product_id', '=', data['product_id']))
        if data.get('journal_id'):
            domain.append(('sheet_id.journal_id', '=', data['journal_id']))

        expenses = self.env['hr.expense'].search(domain)
        lines = []
        for exp in expenses:
            # Handle state (static selection)
            state_selection = exp._fields['state'].selection
            state_dict = dict(state_selection)

            # Handle payment_mode (static selection)
            payment_mode_selection = exp._fields['payment_mode'].selection
            payment_mode_dict = dict(payment_mode_selection)

            # Handle payment_state (dynamic or static)
            if exp.sheet_id:
                ps_field = exp.sheet_id._fields['payment_state']
                ps_selection = ps_field.selection(exp.sheet_id) if callable(ps_field.selection) else ps_field.selection
                payment_state_dict = dict(ps_selection)
            else:
                payment_state_dict = {}

            lines.append({
                'description': exp.sheet_id.name if exp.sheet_id else '',
                'employee': exp.employee_id.name,
                'journal': exp.sheet_id.journal_id.name if exp.sheet_id.journal_id else '',
                'date': exp.date,
                'product': exp.product_id.name,
                "state": state_dict.get(exp.state, exp.state),
                "payment_state": payment_state_dict.get(exp.sheet_id.payment_state, '') if exp.sheet_id else '',
                "payment_mode": payment_mode_dict.get(exp.payment_mode, exp.payment_mode),
                'amount': exp.total_amount,
            })
            
        _logger.info(lines)
        return lines


    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.expense.report.wizard'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.expense.report.wizard',
            'docs': docs,
            'data': data,
            'date_from': data['date_from'],
            'date_to': data['date_to'],
            'get_report_lines': self._get_report_lines,
        }

