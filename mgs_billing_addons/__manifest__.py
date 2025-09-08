# -*- coding: utf-8 -*-
{
    'name': "MGS NECSOM Addons",

    'summary': """
        """,

    'description': """
        
    """,

    'author': "Meisour GS",
    'website': "https://www.meisour.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'mgs_billing',  'mgs_partner_balance', 'mgs_payment_integration', 'mgs_sahal_importing', 'helpdesk'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/property.xml',
        'wizards/create_billing_customer.xml',
        'views/crm.xml',
        'views/test_import.xml',
        'views/bulk_payment.xml',
        'views/balance_transfer.xml',
        'views/res_config.xml',
        'views/report_receipt_and_payment.xml',
        'views/report_calling_report.xml',
        'views/report_tax_report.xml',
        "views/mgs_asset_location_views.xml",
        "views/account_budget_post.xml",
        "views/res_partner.xml",
        'wizards/receipt_and_payment.xml',
        'views/old_sys_sender.xml',
        'wizards/tax_report.xml',
        'wizards/calling_report.xml'
    ],
    # only loaded in demonstration mode

}
