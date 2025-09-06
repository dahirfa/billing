# -*- coding: utf-8 -*-
{
    "name": "MGS Sparkmeter Integration",
    "summary": """
        MGS Sparkmeter Integration
    """,
    "description": """
        MGS Sparkmeter Integration        
    """,
    "author": "Meisour GS",
    "website": "http://www.meisour.com",
    "category": "Billing",
    "version": "18.0",
    # any module necessary for this one to work correctly
    "depends": ["mgs_billing", "mgs_payment_integration"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/reading.xml",
        "views/meters.xml",
        "views/views.xml",
        "views/property.xml",
        "views/menu_items.xml",
    ],
}
