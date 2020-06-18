# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.resource import to_naive_utc, to_naive_user_tz, to_tz

from datetime import datetime

import logging
import re

_logger = logging.getLogger(__name__)

# --------------------- principal ---------------------

# Seguimiento de todos los casos medicos 
class CustomMedicalMonitor (models.Model):
    _name = "custom.medical.monitor"
    _description = "Seguimiento de casos medicos"
    _inherit = ['mail.thread']

    name = fields.Char(string="Nombre caso")
    employee_id = fields.Many2one('hr.employee', string='Empleado', domain=[('active', '=', True)], track_visibility="onchange")
    id_str = fields.Char(string="C.C")
    place_str = fields.Char(string="Lugar de nacimiento")
    tel_str = fields.Char(string="Telefono")
    cel_str = fields.Char(string="Celular")
    job_str = fields.Char( string="Cargo actual")
    des_dep_id = fields.Text('Descripción de cargo actual')
    elem_str = fields.Text('Elementos de proteccion personal')
    gender_str = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string="Género", track_visibility='onchange')
    event_type = fields.Selection([
        ('incidente', 'Incidente'),
        ('accidente', 'Accidente'),
        ('seguimiento', 'Seguimiento de casos médicos')
        ], string='Tipo de caso', track_visibility='onchange')
    worked_time_str = fields.Char(string="Antigüedad")
    usual_posture_str = fields.Char(string="Postura Habitual")
    job_analisys_bool = fields.Boolean('Existen analisis de puesto de trabajo')
    tools_equipment = fields.Text('Herramientas y equipos')
    state = fields.Selection([
        ('draft', 'Nuevo'),
        ('process', 'En proceso'),
        ('finalized', 'Finalizado'),
        ('solved', 'Resuelto'),
        ('reviewed', 'Revisado')
        ], default='draft', string='Estado', track_visibility='onchange')

    # **************** onchange ****************
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.id_str = self.employee_id.identification_id
        self.job_str = self.employee_id.job_id.name
        self.place_str = self.employee_id.x_birth_city_id.name 
        self.cel_str= self.employee_id.x_personal_mobile
        self.gender_str= self.employee_id.gender

    # *************** override ****************
    @api.model
    def create(self, vals):
        now_utc  = datetime.now() # utc cero
        now_user = to_naive_user_tz(now_utc, self.env.user) # datetime.datetime

        employee = self.env['hr.employee'].browse(vals['employee_id'])
        vals['id_str'] = employee.identification_id
        vals['job_str'] = employee.job_id.name 
        vals['place_str'] = employee.x_birth_city_id.name 
        vals['cel_str'] = employee.x_personal_mobile
        vals['gender_str'] = employee.gender

        vals['name'] = vals['event_type'] + " " + str(now_user.date())
        return super(CustomMedicalMonitor, self).create(vals)

    @api.multi
    def unlink(self):
        for mm in self:
            if mm.state in ('reviewed'):
                raise UserError(('No puede borrar el caso %s ya que está revisado') % (mm.name),)
            elif mm.state in ('solved'):
                raise UserError(('No puede borrar el caso %s ya que está resuelto.') % (mm.name), )
            elif mm.state in ('finalized'):
                raise UserError(('No puede borrar el caso %s ya que está finalizado.') % (mm.name), )
            elif mm.state in ('process'):
                raise UserError(('No puede borrar el caso %s ya que está en proceso.') % (mm.name), )
            else:
                return models.Model.unlink(mm)