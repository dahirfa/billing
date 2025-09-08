# -*- coding: utf-8 -*-
{
    "name": "MGS Billing Prepayment",
    "summary": """""",
    "description": """""",
    "author": "Meisour GS",
    "website": "www.meisour.com",
    "category": "Accounting",
    "version": "18.0",
    "depends": [
        "mgs_billing",
        "account",
        "mgs_sparkmeter",
        "mgs_billing_addons",
    ],
    "data": [
        'security/ir.model.access.csv',
        "views/billing_prepayment.xml",
        'views/payment.xml',
        'views/config.xml',
        'views/h_d_automatic_invoice.xml',
        
    ],
    "license": "LGPL-3",
}
