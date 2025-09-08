# -*- coding: utf-8 -*-
{
    'name': "MGS Bulk SMS",
    'summary': """""",
    'description': """""",
    'author': "Meisour GS",
    'website': "www.meisour.com",
    'category': 'Reporting',
    'version': '18.0',
    'depends': ['mgs_billing', 'mgs_sms_integration', 'account', 'mgs_billing_addons'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'license': 'LGPL-3',
}
