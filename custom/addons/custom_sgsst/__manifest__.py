# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Seguridad y salud en el trabajo',
    'summary': 'Gestión general de seguridad y salud en el trabajo.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'hr',
    'version': '0.1',
    'description': """
        Gestión general de seguridad y salud en el trabajo
        """,
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/mail_templates.xml',
        'views/base.xml',
        'views/qs_committee.xml',
        'views/hr_recruitment.xml',
        'views/medical_monitor.xml',
        'views/z_menus.xml',
        # 'views/sgsst_tag.xml',
    ],
    'depends': [
        'base',
        'hr',
        'mail'],
}
