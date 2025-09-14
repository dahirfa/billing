# -*- coding: utf-8 -*-
{
    "name": "Helpdesk API",
    "summary": """
        extends Helpdesk Module with Functionalites relating to billing Module
       """,
    "description": """
    """,
    "author": "Meisour GS",
    "website": "http://www.meisour.com",
    "license": "LGPL-3",
    "category": "Uncategorized",
    "version": "18.0",
    # 'external_dependencies': {
    #     'python': ['google-auth', 'google-auth-oauthlib', 'google-auth-httplib2'],
    # },
    "depends": ["base", "helpdesk", "mgs_billing", "hr"],
    "data": [
        # 'security/ir.model.access.csv',
        "views/views.xml",
        "views/templates.xml",
        "views/stages.xml",
        "views/hr_employee.xml",
    ],
    "demo": [
        "demo/demo.xml",
    ],
}
