# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

# Clase que sobreescribe a los usuarios
# class LoginUserEmail(models.Model):
    # _inherit = ['res.user']

    # @api.onchange('login')
    # def on_change_login(self):
        # if self.login and tools.single_email_re.match(self.login):
            # self.email = self.login
            # pass

# Clase que actualiza responsables con cambio de jefe
class CountryUpdated(models.Model):
    _inherit = 'res.country'

    nationality = fields.Char(string='Nacionalidad')

# Clase que parametriza si se reconoce o no los fines de semana por compañia
class CompanyUpdated(models.Model):
    _inherit = "res.company"

    recognize_saturday = fields.Boolean(string='Reconoce sábados', default=True)
    recognize_sunday   = fields.Boolean(string='Reconoce domingos', default=True)
    report_logo = fields.Binary("Logo facturas", attachment=True, help="Logo presente en facturas",)
