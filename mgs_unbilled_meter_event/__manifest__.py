# -*- coding: utf-8 -*-
{
    "name": "Unbilled Meter Event",
    "summary": """Flag Properties that are accessable for reading""",
    "author": "Meisour GS",
    "website": "https://www.meisour.com",
    "category": "Billing",
    "version": "18.0",
    "depends": ["base", "mgs_billing"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        
        "reports/unbilled_meter_event.xml",
        
        "wizards/mgs_meter_event_wizard.xml",
        
        "views/property.xml",
    ],
}
