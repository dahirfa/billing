# -*- coding: utf-8 -*-
{
    "name": 'Multi Currency Partner Ledger Report',
    "author": "Edge Technologies",
    "version": '17.0',
    "live_test_url": "https://youtu.be/28VZl9SkP1s",
    "images":['static/description/main_screenshot.png'],
    "summary": "Multi currency ledger report multiple currency ledger report partner ledger currency report with multi currency customer ledger partner ledger multi currency report partner ledger report with multi-currency partner ledger based on currency ledger report",
    "description": """This app helps user to print multi currency partner ledger report with filter options like date, target moves, and partner accounts.""",
    "license" : "OPL-1",
    "depends": ['base','account'],
    "data": [
            'security/ir.model.access.csv',

            'reports/report_partnerledger.xml',
            'reports/report.xml',
            'wizard/partner_ledger.xml',
            "views/res_partner.xml",
            
    ],
    "installable": True,
    "auto_install": False,
    "price": 45,
    "currency": "EUR",
    "category": 'Accounting',

}
