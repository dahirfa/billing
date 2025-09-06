# -*- coding: utf-8 -*-
{
    "name": "Tpluspay Integration Necsom",
    "version": "1.0",
    "summary": """Integration of Tpluspay""",
    "author": "Meisour GS",
    "website": "http://www.meisour.com",
    "category": "",
    "depends": ["base", "account", "mgs_payment_integration", "payment", "mgs_integrations_log", 'web'],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/payment_transaction.xml",
        "views/payment_provider.xml",
        "views/confirm.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
