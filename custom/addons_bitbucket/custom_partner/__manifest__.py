# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Contactos - Personalización Colombia',
    'summary': 'Personaliza odoo base "res_partner"',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'Configuración técnica',
    'description': """
        Consta de modificaciones a modelos y funciones que afectan a tarjetas de contacto
        """,
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'depends': [
        'base', 
        'base_address_city',
        'l10n_co',
        'account_base_co'],
}
