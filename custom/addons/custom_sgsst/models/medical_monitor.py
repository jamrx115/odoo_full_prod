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

    # 1 - sección "Investigación Casos de Seguridad y Salud"
    event_type = fields.Selection([
        ('incidente', 'Incidente'),
        ('accidente', 'Accidente'),
        ('seguimiento', 'Seguimiento de casos médicos')
        ], string='Tipo de caso', track_visibility='onchange')
    severity = fields.Selection([
        ('leve', 'Leve'),
        ('grave', 'Grave'),
        ('mortal', 'Mortal')
        ], string='Gravedad', track_visibility='onchange')
    
    # 2- sección "Seguimiento a casos médicos con recomendación o restricción"
    # 2.1 - subsección "Datos Personales"
    employee_id = fields.Many2one('hr.employee', string='Empleado', domain=[('active', '=', True)], track_visibility="onchange")
    date_birth = fields.Date(string="Fecha de nacimiento")
    place_str = fields.Char(string="Lugar de nacimiento")
    id_str = fields.Char(string="C.C")
    gender_str = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string="Género", track_visibility='onchange')
    tel_str = fields.Char(string="Teléfono")
    cel_str = fields.Char(string="Celular")

    # 2.2 - subsección "Información Ocupacional Actual"
    job_str = fields.Char( string="Cargo actual")
    worked_time_str = fields.Char(string="Antigüedad")
    usual_posture_str = fields.Char(string="Postura Habitual")
    job_analisys_bool = fields.Boolean('Existen analisis de puesto de trabajo')
    elem_str = fields.Text('Elementos de protección personal')
    des_dep_id = fields.Text('Descripción de cargo actual')
    tools_equipment = fields.Text('Herramientas y equipos')

    # Pestaña 1 - Información Médica
    diagnosis_str = fields.Text("Diagnóstico")
    diagnosis_date = fields.Date(string="Fecha")
    origin_str = fields.Char("Origen")
    classification_str = fields.Char("Clasificación")
    docs_info = fields.One2many('custom.doctor.information', 'case_id', string="Información de", required=True)

    # Globales
    name = fields.Char(string="Nombre caso")
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
        self.date_birth = self.employee_id.birthday
        self.job_str = self.employee_id.job_id.name
        self.place_str = self.employee_id.x_birth_city_id.name 
        self.cel_str= self.employee_id.x_personal_mobile
        self.gender_str= self.employee_id.gender

        self.des_dep_id = self.employee_id.job_id.description
        self.usual_posture_str = self.employee_id.job_id.x_usual_posture
        self.job_analisys_bool = self.employee_id.job_id.job_analisys_bool
        self.elem_str = self.employee_id.job_id.elem_str
        self.tools_equipment = self.employee_id.job_id.tools_equipment

    # *************** override ****************
    @api.model
    def create(self, vals):
        now_utc  = datetime.now() # utc cero
        now_user = to_naive_user_tz(now_utc, self.env.user) # datetime.datetime

        employee = self.env['hr.employee'].browse(vals['employee_id'])
        vals['id_str'] = employee.identification_id
        vals['date_birth'] = employee.birthday
        vals['job_str'] = employee.job_id.name 
        vals['place_str'] = employee.x_birth_city_id.name 
        vals['cel_str'] = employee.x_personal_mobile
        vals['gender_str'] = employee.gender
        
        vals['des_dep_id'] = employee.job_id.description
        vals['usual_posture_str'] = employee.job_id.x_usual_posture
        vals['job_analisys_bool'] = employee.job_id.job_analisys_bool
        vals['elem_str'] = employee.job_id.elem_str
        vals['tools_equipment'] = employee.job_id.tools_equipment

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

    # ************* state changes *************
    # status draft to process
    @api.multi
    def action_process(self):
        now_utc  = datetime.now() # utc cero
        now_user = to_naive_user_tz(now_utc, self.env.user) # datetime.datetime

        for obj in self:
            if obj.state != 'draft':
                raise UserError('El caso debe estar en estado borrador')
            else:
                obj.write({ 'state': 'process', })
                obj.write({ 'diagnosis_date': now_user.date(), })

    # status process to finalized
    @api.multi
    def action_finalized(self):
        for obj in self:
            if obj.state != 'process':
                raise UserError('El caso debe estar en estado En proceso para finalizarlo.')
            else:
                obj.write({ 'state': 'finalized', })

    # status finalized to solved
    @api.multi
    def action_solved(self):
        for obj in self:
            if obj.state != 'finalized':
                raise UserError('El caso debe estar en estado Finalizado para resolverlo.')
            else:
                obj.write({ 'state': 'solved', })

    # status solved to reviewed
    @api.multi
    def action_reviewed(self):
        for obj in self:
            if obj.state != 'solved':
                raise UserError('El caso debe estar en estado Resuelto para revisarlo.')
            else:
                obj.write({ 'state': 'reviewed', })

class CustomDoctorInformation(models.Model):
    _name = "custom.doctor.information"
    _description = "Información del médico"

    case_id = fields.Many2one('custom.medical.monitor', string="Caso ID")
    entity = fields.Selection([
        ('arp', 'ARP'),
        ('eps', 'EPS'),
        ('empresa', 'Empresa'),
        ('otro', 'Otro'),
        ], string='Entidad', track_visibility='onchange')
    professional_name = fields.Char("Quien (nombre del profesional)")
    professional_job  = fields.Char("Cargo (especialidad)")
    date = fields.Date(string="Fecha", default=datetime.now().date())
