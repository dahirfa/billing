# -*- coding: utf-8 -*-
{
    "name": "Billing Addons",
    "summary": """
    This modules extends on the functionality of the billing Module
        """,
    "description": """
        This modules extends on the functionality of the billing Module
    """,
    "author": "Meisour GS",
    "website": "https://www.meisour.com",
    "category": "Billing",
    "version": "18.0",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "crm",
        "mgs_billing",
        "mgs_partner_balance",
        "mgs_payment_integration",
        "mgs_sahal_importing",
        "helpdesk",
    ],
    # always loaded
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/property.xml",
        "wizards/create_billing_customer.xml",
        "views/crm.xml",
        "views/bulk_payment.xml",
        "views/balance_transfer.xml",
        "views/res_config.xml",
        "views/report_receipt_and_payment.xml",
        "views/report_calling_report.xml",
        "views/mgs_asset_location_views.xml",
        "views/res_partner.xml",
        "wizards/receipt_and_payment.xml",
        "views/old_sys_sender.xml",
        "wizards/calling_report.xml",
    ],
    # only loaded in demonstration mode
}
