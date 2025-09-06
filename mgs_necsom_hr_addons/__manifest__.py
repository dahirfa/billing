# -*- coding: utf-8 -*-
{
    'name': "Human Resource Addons",
    'author': "Meisour Solutions",
    'website': "https://www.meisour.com",
    'category': 'Human Resources/Payroll',
    'version': '0.1',
    'depends': ['base','hr','hr_payroll','account'],
        'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/mgs_payslp_run.xml',
    ],
}
