# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Calidad de servicios y procesos',
    'summary': 'Gestión general de Calidad de servicios y procesos.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'Sales',
    'version': '0.1',
    'description': """
        Gestión general de Calidad de servicios y procesos
        """,
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/pqrs.xml',
        'views/analysis.xml',
        'views/update_pqrs_form.xml',
        'views/z_menus.xml',
    ],
    'depends': [
        'base',
        'mail',
        'project'],
}
