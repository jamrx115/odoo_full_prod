# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Módulo para nuevos modelos y vistas',
    'summary': 'Personaliza odoo base con modelos nuevos a los bases o de terceros.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'Configuración técnica',
    'description': """
        Consta de  modelos nuevos y modificados que afectan a las demás aplicaciones de manera transversal
        """,
    'data': [
        #'security/ir.model.access.csv',
        'views/views.xml',
        'views/theme_alltic.xml',
    ],
    'depends': ['base', 'base_address_city', 'hr', 'resource', 'web', 'website'],
}
