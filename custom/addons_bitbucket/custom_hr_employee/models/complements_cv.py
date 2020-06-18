# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, tools
from datetime import datetime, timedelta
import logging
import pytz
import time
import re

_logger = logging.getLogger(__name__)

# proyectos en la hoja de vida
class HrProyects(models.Model):
    _name = 'hr.project'
    _description = "Proyectos del empleado"

    def _default_year(self):
      hoy = datetime.now(tz=pytz.timezone(self.env.user.partner_id.tz)).date() # tipo date
      return hoy.year

    name = fields.Char('Proyecto', required=True, help="Nombre del proyecto")
    employee_id = fields.Many2one('hr.employee',
                                  string='Empleado',
                                  required=True)
    description = fields.Text('Descripción', help="Descripción del proyecto")    
    role = fields.Char('Rol desempeñado', help="Ej: Project Manager, Team Member, Resource Manager, Stakeholder.")
    year = fields.Integer('Año finalización', default=_default_year)
    customer = fields.Char('Cliente final')

    _sql_constraints = [
        ('_check_year_limits', 'CHECK(year>1899 AND year<=extract(YEAR FROM now()))', 'Error! El año debe tener 4 dígitos, máximo el año actual'),
    ]

    @api.multi
    @api.constrains('year')
    def _check_year_limits(self):
        for record in self:
            if record.year < 1900 or record.year > self._default_year() :
                raise ValidationError(_('El año debe ser mínimo 1900 y máximo el año actual.'))

# proyectos en la hoja de vida
class HrSkills(models.Model):
    _name = 'hr.skills'
    _description = "Habilidades y herramientas del empleado"

    name = fields.Char('Habilidad o Herramienta', required=True, help="Habilidad / herramienta")
    employee_id = fields.Many2one('hr.employee',
                                  string='Empleado',
                                  required=True)
    level = fields.Selection([
            ('basico', 'Básico'),
            ('medio', 'Intermedio'),
            ('avanzado', 'Avanzado')
        ], string='Nivel', required=True)

# herencia a modelo Empleado
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    projects_ids = fields.One2many('hr.project',
                                   'employee_id',
                                   'Proyectos realizados')
    skills_ids = fields.One2many('hr.skills',
                                     'employee_id',
                                     'Habilidades y herramientas')
