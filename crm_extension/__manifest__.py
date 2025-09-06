# -*- coding: utf-8 -*-
{
    "name": "CRM Extension",
    "summary": """
      """,
    "description": """
        
    """,
    "author": "Meisour GS",
    "website": "http://www.meisour.com",    
    "category": "CRM",
    "version": "18.0",
    "depends": ["base", "crm", "mgs_billing", "sale", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/templates.xml",
        "views/report_print_opportunity.xml",
        "wizard/print_opportunity.xml",
    ],
    "demo": [
        "demo/demo.xml",
    ],
}
