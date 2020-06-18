# -*- coding: utf-8 -*-
{
    'name': 'account_extra_co',

    'summary': '',
        

    'description': 'Pide tercero, analitica y base en cuenta',

    'author': "OpenSoftIT S.A.S.",
    
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
