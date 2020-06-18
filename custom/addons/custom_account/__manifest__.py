# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Contabilidad - Personalizaciones',
    'summary': 'Personaliza contabilidad.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'Accounting',
    'description': """
        Consta de modificaciones a sus modelos y funciones
        """,
    'data': [
        'security/ir.model.access.csv',
        'views/account.xml',
        'views/report_account_invoice.xml',
        'views/crm.xml',
    ],
    'depends': ['base', 
                'hr', 
                'account', 
                'account_asset', 
                'account_base_co', 
                'analytic', 
                'crm', 
                'web'],
}
