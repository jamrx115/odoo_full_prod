# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright (C) Innovatecsa SAS e Interconsulting SA
# Authors       Over Garcia Caballero, gerencia@innovatecsa.com
#               Jose Alfredo Lopez, gerencia@interconsulting.com
{
    'name' : 'Fiscal Year Colombian',
    'version' : '1.1',
    'author' : 'OpenSoftIT S.A.S.',
    'category' : 'Accounting & Finance',
    'description' : """
Accounting and Financial Management.
====================================

Financial and accounting module that covers:
--------------------------------------------
    * Fiscal year
    * Account types
    * Fiscal year close
    """,
    'website': '',
    'depends' : ['account', ],
    'data': [        
        #'wizard/account_fiscalyear_close_view.xml',
        #'wizard/account_period_close_view.xml',
        #'wizard/account_fiscalyear_close_state.xml',        
        #'wizard/account_open_closed_fiscalyear_view.xml',        
        'views/account_fiscal_year.xml',
        'data/account_data.xml', 
        'security/ir.model.access.csv',
    ],
    'qweb' : [

    ],
    'demo': [

    ],
    'test': [

    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
