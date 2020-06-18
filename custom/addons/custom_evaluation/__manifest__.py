# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Evaluaciones de Entrenamiento',
    'summary': 'Módulo que permite realizar evaluaciones de entrenamiento.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'hr',
    'description': """
        Módulo que permite realizar evaluaciones sobre algún tema en específico,
        agregando el contenido y luego asignando su respectiva evaluación
        """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/at_subtype.xml',
        'views/at_evaluation.xml',
        'views/at_evaluation_result.xml',
        'views/at_evaluation_templates.xml',
    ],
    'depends': ['base', 'base_address_city', 'hr', 'website', 'custom_performance'],
}
