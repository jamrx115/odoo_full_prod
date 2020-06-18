# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Empleados - Personalizaciones',
    'summary': 'Personaliza el modelo empleado.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'hr',
    'description': """
        Consta de modificaciones al modelo empleado y sus funciones
        """,
    'data': [
        'security/ir.model.access.csv',
        'security/hr_security.xml',
        'views/hr_contract.xml',
        'views/hr_employee.xml',
        'views/hr_projects.xml',
        'views/hr_skills.xml',
        'views/report_curriculum_vitae.xml',
        'views/reports_and_charts.xml',
    ],
    'depends': [
        # base: employee, user
        'base', 'hr',
        # base: cities
        'base_address_city',
        # base: contracts
        'hr_contract', 
        # 3ros: hr.emergency.contact, emails passport
        #       personal_mobile, joining_date, passport_expiry_date
        'hr_employee_updation',
        # base: schedule
        'resource'],
}
