# -*- coding: utf-8 -*-
from odoo import http

# class AccountExtraCo(http.Controller):
#     @http.route('/account_extra_co/account_extra_co/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_extra_co/account_extra_co/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_extra_co.listing', {
#             'root': '/account_extra_co/account_extra_co',
#             'objects': http.request.env['account_extra_co.account_extra_co'].search([]),
#         })

#     @http.route('/account_extra_co/account_extra_co/objects/<model("account_extra_co.account_extra_co"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_extra_co.object', {
#             'object': obj
#         })