# -*- coding: utf-8 -*-
{
    "name": "Billing Addons",
    "summary": """This modules extends on the functionality of the billing Module""",
    "description": """This modules extends on the functionality of the billing Module""",
    "author": "Meisour GS",
    "website": "https://www.meisour.com",
    "category": "Billing",
    "version": "18.0",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "crm",
        "mgs_billing",
    ],
    # always loaded
    "data": [
        "views/property.xml",
        "views/crm.xml",
        "wizards/create_billing_customer.xml",
    ],
    # only loaded in demonstration mode
}
