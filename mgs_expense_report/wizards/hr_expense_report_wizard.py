# -*- coding: utf-8 -*-
from odoo import api, fields, models
import time
class HrExpenseReportWizard(models.TransientModel):
    _name = 'hr.expense.report.wizard'
    _description = 'HR Expense Report Wizard'

    product_id = fields.Many2one(
        'product.product',
        string="Category",
        domain=[('can_be_expensed', '=', True)]
    )
    journal_id = fields.Many2one(
        'account.journal',
        string="Journal",
        domain=[('type','in',['cash', 'bank'])]
        
    )
    
    
    date_from = fields.Date(string="Start Date", required=True, default=fields.Date.today().replace(day=1))
    date_to = fields.Date(string="End Date", required=True, default=fields.Date.today())

    def action_print_report(self):
        data = {
            'product_id': self.product_id.id if self.product_id else False,
            'journal_id': self.journal_id.id if self.journal_id else False,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return self.env.ref('mgs_expense_report.report_hr_expense_report').report_action(self, data=data)

