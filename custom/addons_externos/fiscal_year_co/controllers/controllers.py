# -*- coding: utf-8 -*-
from odoo import http

# class FiscalYearCo(http.Controller):
#     @http.route('/fiscal_year_co/fiscal_year_co/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fiscal_year_co/fiscal_year_co/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fiscal_year_co.listing', {
#             'root': '/fiscal_year_co/fiscal_year_co',
#             'objects': http.request.env['fiscal_year_co.fiscal_year_co'].search([]),
#         })

#     @http.route('/fiscal_year_co/fiscal_year_co/objects/<model("fiscal_year_co.fiscal_year_co"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fiscal_year_co.object', {
#             'object': obj
#         })