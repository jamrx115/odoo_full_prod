# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Proyectos - Personalizaciones',
    'summary': 'Personaliza odoo base "project"',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'Project',
    'description': """
        Consta de modificaciones a modelos y funciones que afectan a proyectos y tareas
        """,
    'data': [
        'views/views.xml',
    ],
    'depends': [
        'base', 
        'project'],
}
