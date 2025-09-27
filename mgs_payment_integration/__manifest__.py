# -*- coding: utf-8 -*-
{
    "name": "Payment Integration Base",
    "summary": """Payment Integration Base""",
    "description": """""",
    "author": "Meisour GS",
    "website": "http://www.meisour.com",
    "category": "Payment",
    "version": "0.1",
    "depends": ["base", "account", "payment", "mail"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        
        "reports/receipt_and_payment_summary.xml",
        "reports/receipt_and_payment_detailed.xml",
        "reports/payment_receipt.xml",
        "reports/receipt_and_payment.xml",
        
        "views/payment_integration.xml",
        "wizards/receipt_and_payment.xml",
        "views/bulk_payment.xml",
        "views/res_config.xml",
        
        "wizards/receipt_and_payment.xml",
    ],
}
