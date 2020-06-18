# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Experiencias y Certificaciones',
    'summary': 'Personaliza experiencias académicas, profesionales y certificaciones.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'hr',
    'description': """
        Consta de modificaciones a los modelos experiencias académicas, profesionales y certificaciones y sus funciones
        """,
    'data': [
        'views/hr_certification.xml',
        'views/hr_academic.xml',
        'views/hr_experience.xml',
    ],
    'depends': [
        'base', 'hr',
        'base_address_city',
        'hr_experience'],
}
