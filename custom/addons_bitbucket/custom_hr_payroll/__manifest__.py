# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Nómina - Personalizaciones',
    'summary': 'Personaliza hr_payroll.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'hr',
    'description': """
        Consta de modificaciones a sus modelos y funciones
        """,
    'data': [
        'views/views_base.xml',
        'views/views_qweb.xml',
    ],
    'depends': ['base', 'hr', 'hr_payroll'],
}
