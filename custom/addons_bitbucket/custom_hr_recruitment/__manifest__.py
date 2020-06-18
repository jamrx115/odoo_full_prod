# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Reclutamiento - Personalizaciones',
    'summary': 'Personaliza reclutamiento y candidatos.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'hr',
    'description': """
        Consta de modificaciones a sus modelos y funciones
        """,
    'data': [
        'views/hr_employee.xml',
    ],
    'depends': [
        'base', 'hr', 
        'base_address_city', 
        'hr_recruitment'],
}
