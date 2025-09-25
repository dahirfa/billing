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
        "helpdesk",
        "mgs_helpdesk_api"
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "wizards/create_helpdesk_ticket_wizard.xml",
        "views/property.xml",
        "views/crm.xml",
        "views/res_config.xml",
        "wizards/create_billing_customer.xml",
    ],
    # only loaded in demonstration mode
}
