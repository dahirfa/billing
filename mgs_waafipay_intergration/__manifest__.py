# -*- coding: utf-8 -*-
{
    "name": "Waafipay Integration",
    "version": "1.0",
    "summary": """Integration of waafipay
        It Supports: 
        EVCPlus	Hormuud Telecom	
        ZAAD Service	Telesom	
        SAHAL Service	Golis Telecom
        WAAFI Djibouti	WAAFI	
        WAAFI International	WAAFI
    """,
    "author": "Meisour GS",
    "website": "http://www.meisour.com",
    "category": "",
    "depends": ["base", "account", "mgs_payment_integration", "payment", 'mgs_integrations_log'],
    "data": [
        "data/data.xml",
        "views/payment_transaction.xml",
        "views/payment_provider.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
