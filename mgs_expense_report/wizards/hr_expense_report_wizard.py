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
    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)

    @api.model
    def default_get(self, fields):
        res = super(HrExpenseReportWizard, self).default_get(fields)
        today = time.strftime("%Y-%m-01")
        if int(time.strftime('%m') == 1 or time.strftime('%m') == 3 or time.strftime('%m') == 5 or time.strftime(
                '%m') == 7 or time.strftime('%m') == 8 or time.strftime('%m') == 10 or time.strftime('%m') == 12):
            lastday = time.strftime("%Y-%m-31")
        elif int(time.strftime('%m')) == 2:
            if (int(time.strftime('%Y')) % 4) == 0:
                lastday = time.strftime("%Y-%m-29")
            else:
                lastday = time.strftime("%Y-%m-28")
        else:
            lastday = time.strftime("%Y-%m-30")
        res.update({'date_from': today, 'date_to': lastday})
        return res
    def action_print_report(self):
        data = {
            'product_id': self.product_id.id if self.product_id else False,
            'journal_id': self.journal_id.id if self.journal_id else False,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return self.env.ref('mgs_expense_report.report_hr_expense_report').report_action(self, data=data)

