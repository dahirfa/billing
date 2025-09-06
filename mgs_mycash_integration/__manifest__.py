# -*- coding: utf-8 -*-
{
    'name': "MGS MyCash Payment Integration",

    'summary': """
        """,

    'description': """
        
    """,

    'author': "Meisour GS",
    'website': "http://www.meisour.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Payment',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'mgs_payment_integration', 'payment', 'mgs_user_access_token'],

    # always loaded
    'data': [
        'data/data.xml',
        'views/views.xml',
    ],
}
