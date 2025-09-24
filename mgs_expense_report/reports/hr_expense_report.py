from odoo import models

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
            lines.append({
                'description': exp.sheet_id.name if exp.sheet_id else '',
                'employee': exp.employee_id.name,
                'journal': exp.sheet_id.journal_id.name if exp.sheet_id.journal_id else '',
                'date': exp.date,
                'product': exp.product_id.name,
                'amount': exp.total_amount,
            })
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

