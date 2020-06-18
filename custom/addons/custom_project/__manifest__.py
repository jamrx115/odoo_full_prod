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
        'security/ir.model.access.csv',
        'views/project_project.xml',
        'views/project_hr_timesheet.xml',
        'views/project_new.xml',
    ],
    'depends': [
        'base',
        'hr_timesheet',
        'project'],
}
