# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
import xlsxwriter
import base64
from io import BytesIO
_logger = logging.getLogger(__name__)


class Accounting_reportPartner_ledger(models.TransientModel):
    _name = "multicurrency.partnerledger"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        readonly=True,
        default=lambda self: self.env.user.company_id,
    )
    currency_ids = fields.Many2many(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env["res.currency"].search([]),
    )
    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")
    target_move = fields.Selection(
        [
            ("posted", "All Posted Entries"),
            ("all", "All Entries"),
        ],
        string="Target Moves",
        required=True,
        default="posted",
    )
    reconciled = fields.Boolean("Show Initial Balance", default=True)
    result_selection = fields.Selection(
        [
            ("customer", "Receivable Accounts"),
            ("supplier", "Payable Accounts"),
            ("customer_supplier", "Receivable and Payable Accounts"),
        ],
        string="Partner's Account",
        required=True,
        default="customer",
    )
    partner_ids = fields.Many2many(
        "res.partner",
        "rel_multicurrency_partner",
        "multicurrency_id",
        "partner_id",
        string="Partner's",
    )

    category_id = fields.Many2many(
        "res.partner.category",
        column1="partner_id",
        column2="category_id",
        string="Tags",
    )
    
    
    display_zero_values = fields.Boolean(
        string='Display Zero Values?',
    )
    

    summary = fields.Boolean(
        string="Summary",
    )

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)


    def get_data(self):
        data = {}
        used_context = {"currency_ids": [a.id for a in self.currency_ids]}
        data["move_state"] = ["draft", "posted"]
        if self.target_move == "posted":
            data["move_state"] = ["posted"]
        result_selection = self.result_selection
        if result_selection == "supplier":
            data["account_type"] = ["supplier"]
        elif result_selection == "customer":
            data["account_type"] = ["customer"]
        else:
            data["account_type"] = ["customer", "supplier"]

        data["date_from"] = self.date_from
        data["date_to"] = self.date_to

        return {
            "data": data,
            "docs": self.partner_ids.ids,
            "target_move": self.target_move,
            "account_type": self.result_selection,
            "reconciled": self.reconciled,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "summary": self.summary,
            'category_id':self.category_id.ids,
            'display_zero_values':self.display_zero_values
        }
    
   

    def print_partner_ledger(self):
        data = {}
        used_context = {"currency_ids": [a.id for a in self.currency_ids]}
        data["move_state"] = ["draft", "posted"]
        if self.target_move == "posted":
            data["move_state"] = ["posted"]
        result_selection = self.result_selection
        if result_selection == "supplier":
            data["account_type"] = ["supplier"]
        elif result_selection == "customer":
            data["account_type"] = ["customer"]
        else:
            data["account_type"] = ["customer", "supplier"]

        data["date_from"] = self.date_from
        data["date_to"] = self.date_to

        final_dict = {
            "data": data,
            "used_context": used_context,
            "docs": self.partner_ids.ids,
            "target_move": self.target_move,
            "account_type": self.result_selection,
            "reconciled": self.reconciled,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "summary": self.summary,
            'category_id':self.category_id.ids,
            'display_zero_values':self.display_zero_values
        }

        return (
            self.env.ref(
                "multi_currency_partner_ledger_app.multi_currency_partner_ledger"
            )
            # .with_context(used_context)
            .report_action(self, data=final_dict)
        )


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
