# -*- coding: utf-8 -*-
{
    "name": "Billing",
    "summary": """Meisour Custome Billing Module""",
    
    "description": """
        This module transforms Odoo into a powerful utility billing platform,
        designed for companies that bill customers based on their consumption of services.
        By integrating seamlessly with Odoo's existing accounting and CRM applications, 
        it provides a comprehensive solution for meter management, 
        automated billing, and customer service.
    """,
    
    "author": "Meisour GS",
    "website": "https://www.meisour.com",
    "category": "Billing",
    "version": "18.0",
    "depends": ["base", "mail", "product", "account", "crm"],
    
    
    "data": [
        "data/seq.xml",
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        
        
        "reports/collection_report.xml",
        "reports/billing_sale.xml",
        "reports/all_reveivables.xml",
        "reports/billed_percentage.xml",
        "reports/billing_receipt.xml",
        "reports/connect_disconnect.xml",
        "reports/meter_cubic_sold.xml",
        "reports/get_monthes_due.xml",
        "reports/property_log_rep.xml",
        "reports/calling_report.xml",
        
        
        "wizards/all_receivables_wiz.xml",
        "wizards/billed_percentage_wiz.xml",
        "wizards/connect_disconnect_wiz.xml",
        "wizards/collection_report_wiz.xml",
        "wizards/meter_cubic_sold_wiz.xml",
        "wizards/apply_extra_charge_wiz.xml",
        "wizards/con_desc_comment.xml",
        "wizards/get_monthes_due.xml",
        "wizards/property_log_wiz.xml",
        "wizards/calling_report.xml",
        "wizards/create_billing_customer.xml",
        
        "views/billing_customer.xml",
        "views/billing_account.xml",
        "views/collector.xml",
        "views/zone.xml",
        "views/property.xml",
        "views/property_type.xml",
        "views/guarantor.xml",
        "views/meters.xml",
        "views/reset_meter.xml",
        "views/product.xml",
        "views/reading.xml",
        "views/meter_reading.xml",
        "views/document_type.xml",
        "views/crm.xml",
        "views/res_config.xml",
        "views/mgs_billing_menu.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
}
