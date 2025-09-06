# -*- coding: utf-8 -*-
{
    "name": "MGS Premier Payment Integration",
    "version": "0.1",
    "summary": """Premier Integration""",
    "author": "Meisour GS",
    "website": "http://www.meisour.com",
    "category": "Payment",
    "depends": [
        "base",
        "account",
        "mgs_payment_integration",
        "payment",
        "mgs_integrations_log",
    ],
    # always loaded
    "data": [
        "data/data.xml",
        "views/views.xml",
    ],
}
