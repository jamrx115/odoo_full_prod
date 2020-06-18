# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Partes de Horas - Personalizaciones',
    'summary': 'Personaliza odoo base "hr_timesheet"',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'Hidden/Dependency',
    'description': """
        Consta de modificaciones a modelos y funciones que afectan a registros de partes de horas
        """,
    'data': [
        'views/analytic_hr_timesheet.xml',
    ],
    'depends': [
        'analytic',
        'hr_payroll',
        'hr_timesheet',
        'custom_project'],
}
