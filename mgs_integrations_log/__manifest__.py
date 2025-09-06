# -*- coding: utf-8 -*-
{
    'name': 'Integrations Error Log',
    'version': '1.0',
    'summary': """Used To Log Erros From Integrated Modules""",
    'author': "Meisour GS",
    'website': "www.meisour.com",
    'category': 'Generic',
    'depends': ['base', 'mail'],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/mgs_integration_log_views.xml",
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
