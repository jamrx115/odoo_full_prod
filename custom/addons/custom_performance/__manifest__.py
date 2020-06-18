# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Evaluaciones de Desempeño | Objetivos',
    'summary': 'Gestiona los objetivos para las evaluaciones de desempeño.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'hr',
    'version': '0.1',
    'description': """
        Gestiona los objetivos para las evaluaciones de desempeño
        """,
    'data': [
        'security/custom_performance_security.xml',
        'security/ir.model.access.csv',
        'views/performance.xml',
    ],
    'depends': [
        'base', 'hr',
        'base_address_city',
        'mail',
        'web_widget_timepicker'],
}
