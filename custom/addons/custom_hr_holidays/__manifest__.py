# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Ausencias - Personalizaciones',
    'summary': 'Personaliza hr_holidays.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'hr',
    'description': """
        Consta de modificaciones a sus modelos y funciones
        """,
    'data': [
        'security/group_by_department.xml',
        'security/ir.model.access.csv',
        'views/mail_templates.xml',
        'views/views_hr_holidays.xml',
        'views/views_hr_holidays_status.xml',
        'views/wizzard.xml',
        'views/report_holiday_template.xml',
        'views/report_menu.xml',
    ],
    'depends': ['base', 'hr', 'hr_holidays'],
}
