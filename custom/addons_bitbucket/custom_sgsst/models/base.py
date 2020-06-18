# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools
from odoo.exceptions import UserError, ValidationError

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

import logging
import pytz
import time
import re

_logger = logging.getLogger(__name__)

# --------------------- configurables ---------------------

# Periodo
class CustomPeriod(models.Model):
    _name = "custom.period"
    _description = "Periodo comité"
    _inherit = ['mail.thread']
    _order = "year desc, period_sel desc"

    def _default_year(self):
      hoy = datetime.now(tz=pytz.timezone(self.env.user.partner_id.tz)).date() # tipo date
      return hoy.year

    year = fields.Integer('Año', default=_default_year)
    period_sel = fields.Selection([
        ('1','1'),
        ('2','2')
        ], 
        string="Periodo", track_visibility="onchange")
    name = fields.Char(string="Nombre")

    _sql_constraints = [
        ('_check_year_limits', 'CHECK(year>1899 AND year<=extract(YEAR FROM now()))', 'Error! El año debe tener 4 dígitos, máximo el año actual'),
        ('_check_name_unique', 'UNIQUE(name)', 'El periodo ya fue registrado')
    ]

    @api.multi
    @api.constrains('year')
    def _check_year_limits(self):
        for record in self:
            if record.year < 1900 or record.year > self._default_year() :
                raise ValidationError(_('El año debe ser mínimo 1900 y máximo el año actual.'))

    @api.multi
    @api.onchange('period_sel')
    def _onchange_name(self):
    	for record in self:
    		if record.period_sel:
        		record.name = str(record.year) + ' (' + record.period_sel+ ')'

# --------------------- principal ---------------------

# Candidatos a comités
class CustomCommitteeApplicant(models.Model):
    _name = "custom.committee.applicant"
    _description = "Candidatos a comités"
    _inherit = ['mail.thread']

    type_comm = fields.Selection([
        ('COPASST','COPASST'),
        ('BE','Brigada de emergencia'),
        ('CC','Comité de convivencia')
        ], 
        string="Tipo de comité", track_visibility="onchange")
    type_brig = fields.Selection([
        ('ER','Evacuación y rescate'),
        ('PA','Primeros auxilios'),
        ('MF','Manejo de fuego')
        ], 
        string="Tipo de brigada de emergencia", track_visibility="onchange")
    period_id = fields.Many2one('custom.period', string='Periodo', track_visibility="onchange")
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    job_str = fields.Char(string="Cargo")
    company_str = fields.Char(string="Empresa")
    state = fields.Selection([
        ('draft','Borrador'),
        ('inscrito','Inscrito(a)'),
        ('activo','Activo(a)'),
        ('retirado','Retirado(a)')
        ], 
        string="Estado", default='draft', track_visibility="onchange")
    name = fields.Char(string="Candidato")

    _sql_constraints = [
        ('_check_name_unique', 'UNIQUE(name)', 'El candidato ya fue registrado para el periodo y comité seleccionados')
    ]

    # **************** onchange ****************
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.job_str = self.employee_id.job_id.name
        self.company_str = self.employee_id.company_id.name

    # *************** override ****************
    @api.model
    def create(self, vals):
        # obligatorios
        name = vals.get('type_comm')
        employee = self.env['hr.employee'].browse(vals.get('employee_id'))
        p = self.env['custom.period'].browse(vals.get('period_id')).name
        # opcional
        b = vals.get('type_brig')
        # construcción nombre
        if b:
            name += " " + b
        name += " " + p + " - " + employee.name
        vals['name'] = name
        vals['job_str'] = employee.job_id.name
        vals['company_str'] = employee.company_id.name

        return super(CustomCommitteeApplicant, self).create(vals)

    #@api.multi
    #def write(self, values):
        #if values.get('employee_id') or values.get('type_comm'):
            # recalcular nombre
            #name = vals.get('type_comm')
        #res = super(CustomQsCommittee, self).write(values) # bool
        #return res

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state in ('activo'):
                raise UserError(('No puede borrar el candidato dado que está ejerciendo sus labores'))
            elif obj.state in ('retirado'):
                raise UserError(('No puede borrar el candidato dado que ya ejerció sus labores'))
            else:
                return models.Model.unlink(obj)

    # status inscrito to activo
    @api.multi
    def action_start(self):
        for obj in self:
            if obj.state != 'draft':
                raise UserError('El registro debe estar en estado borrador para inscribir al candidato.')
            obj.write({ 'state': 'inscrito', })

    # status inscrito to activo
    @api.multi
    def action_choose(self):
        for obj in self:
            if obj.state != 'inscrito':
                raise UserError('El candidato debe estar inscrito para iniciar labores en su comité.')
            obj.write({ 'state': 'activo', })

    # status activo to retirado
    @api.multi
    def action_remove(self):
        for obj in self:
            if obj.state != 'activo':
                raise UserError('El candidato debe estar activo para retirarse de sus labores en el comité respectivo.')
            obj.write({ 'state': 'retirado', })
