# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Evaluaciones de Desempeño | Capacitaciones',
    'summary': 'Gestiona las capacitaciones para desarrollo de talento humano.',
    'author': 'Alltic SAS',
    'website': 'https://alltic.co',
    'category': 'hr',
    'version': '0.1',
    'description': """
        Gestiona el flujo de aprobación de capacitaciones para desarrollo de talento humano
        """,
    'data': [
        'data/report_paperformat_knowledge.xml',
        'security/custom_knowledge_security.xml',
        'security/ir.model.access.csv',
        'data/knowledge_template_mail.xml',
        'data/reasons_data.xml',
        'views/knowledge.xml',
        'views/report_pdf_training_eva.xml',
        'views/reports_pdf.xml',
    ],
    'depends': [
        'base', 'hr',
        'base_address_city',
        'mail',
        'custom_hr_experience',
        'custom_performance'],
}
