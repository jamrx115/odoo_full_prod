# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'CRM - Personalizaciones',
    'summary': 'Personaliza CRM.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'Sales',
    'description': """
        Consta de modificaciones a sus modelos y funciones
        """,
    'data': [
        'views/crm.xml',
    ],
    'depends': ['base',
                'crm'],
}
