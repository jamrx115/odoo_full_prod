# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, tools
import logging
import pytz
import re

_logger = logging.getLogger(__name__)

# Clase que actualiza campos o metodos
class HrCurriculumUpdated(models.Model):
    _inherit = 'hr.curriculum'

    # actualizando campo proveedor
    partner_id = fields.Many2one('res.partner',
                                 'Proveedor',
                                 domain="[('supplier', '=', True)]",
                                 help="Empleador, Universidad, Autoridad Certificadora")

# Nueva clase para tipificar certificados
class TypeCertification(models.Model):
    _name = "custom.type.certification"
    _description = "Tipo Certificación"

    name = fields.Char(string='Nombre',required=True)

 # Nueva clase para niveles de certificados
class LevelCertification(models.Model):
    _name = "custom.level.certification"
    _description = "Nivel Certificación"

    name = fields.Char(string='Nombre',required=True)
    type_cert_id = fields.Many2one('custom.type.certification', string='Tipo', required=True,
                                   help="Tipo Certificación.")

# Clase que actualiza campos o metodos
class HrCertificationUpdated(models.Model):
    _inherit = 'hr.certification'

    type_cert_id = fields.Many2one('custom.type.certification', string='Tipo',
                                   help="Tipo Certificación.")
    level_cert_id = fields.Many2one('custom.level.certification', string='Nivel',
                                   help="Nivel Certificación.")