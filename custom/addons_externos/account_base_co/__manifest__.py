# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Account Base Colombian',
    'summary': 'Digit of verification,Ciiu,State,City',
    'author': 'OpenSoft IT S.A.S.',
    'description': """
        creates first name, middle name, first last name and 
        second last name in customers who are not companies,
        Digit of verification,Ciiu,State,City
        """,
    #'website': '',
    'version': '11.0.1.0.0',
    'category': 'Localization',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/res.ciiu.csv',
        'data/res_country_data.xml',
        'data/res.country.state.csv',
        'data/res.bank.csv',        'views/res_ciiu_view.xml',
        'views/res_partner_view.xml',
        'views/res_country_view.xml',
        'views/account_journal_view.xml',
        'views/account_invoice_view.xml',
    ],
 
    'installable': True,
    'auto_install': False,
    'application' : True,
}
