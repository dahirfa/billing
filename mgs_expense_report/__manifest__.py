# -*- coding: utf-8 -*-
{
    'name': 'Mgs_expense_report',
    'version': '1.0.0',
    'summary': """ Mgs_expense_report Summary """,
    'author': 'Meisour GS',
    'website': 'https://www.meisour.com',
    'category': '',
    'depends': ['base', 'web','hr_expense'],
    "data": [
        "security/ir.model.access.csv",
        "reports/hr_expense_report.xml",
        "wizards/hr_expense_report_wizard.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
