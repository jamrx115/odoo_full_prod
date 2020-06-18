# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
import logging
import re

_logger = logging.getLogger(__name__)
# _logger.debug('---------------')
# _logger.debug('day_intervals 0 %s', day_intervals[0])

#clase creada por alltic que crea codigo para regla salarial desde tipo de ausencia
class HolidayStatusCode(models.Model):
    _inherit = 'hr.holidays.status'

    code = fields.Char('Código para regla salarial')

    @api.multi
    @api.onchange('code')
    def _check_code(self):
        if self.code:
            pattern = "^[A-Z0-9]{3,7}$"
            if re.match(pattern, self.code) == None:
                self.code = ""
                return {
                    'warning': {'title': 'Error',
                                'message': 'Formato de código no valido, debe incluir términos alfanúmeros y guion (si aplica) y longitud 3 a 7 caracteres', }
                }
