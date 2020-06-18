# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, tools
from datetime import datetime, timedelta
import logging
import pytz
import re

_logger = logging.getLogger(__name__)

# Clase que actualiza campos o metodos
class HrEmployeeUpdated(models.Model):
    _inherit = 'hr.employee'

    # ---------- Override fields
    address_id = fields.Many2one('res.partner', 'Oficina', groups="base.group_user")
    work_email = fields.Char('Correo electrónico del trabajo', readonly=True, groups="base.group_user")
    mobile_phone = fields.Char('Móvil del trabajo', readonly=True, groups="base.group_user")
    work_phone = fields.Char('Teléfono fijo del trabajo', readonly=True, groups="base.group_user")
    department_id = fields.Many2one('hr.department', 'Departamento', readonly=True, groups="base.group_user")
    job_id = fields.Many2one('hr.job', 'Cargo', readonly=True, groups="base.group_user")
    parent_id = fields.Many2one('hr.employee', 'Responsable', readonly=True, groups="base.group_user")
    coach_id = fields.Many2one('hr.employee', 'Monitor', readonly=True, groups="base.group_user")
    manager = fields.Boolean(string='Es jefe', readonly=True, groups="base.group_user")

    country_id = fields.Many2one('res.country', 'Nationality (Country)', groups="base.group_user")

    identification_id = fields.Char(string='Identification No', groups="base.group_user")
    passport_id = fields.Char('Passport No', groups="base.group_user")
    permit_no = fields.Char('Work Permit No', groups="base.group_user")
    visa_no = fields.Char('Visa No', groups="base.group_user")
    visa_expire = fields.Date('Visa Expire Date', groups="base.group_user")

    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', groups="base.group_user", default='single')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], default=False, groups="base.group_user")
    children = fields.Integer(string='Number of Children', groups="base.group_user")

    birthday = fields.Date('Date of Birth', groups="base.group_user")

    # ---------- Override funciones

    # escritura automática de jefes inmediatos
    @api.onchange('department_id')
    def _onchange_department(self):
        jefe_inmediato_id = self.department_id.manager_id.id
        empleado_id = self._origin.id
        if (jefe_inmediato_id != None) and (jefe_inmediato_id != empleado_id):
            self.parent_id = self.department_id.manager_id
        else:
            jefe_superior_id = self.department_id.parent_id.manager_id.id
            if jefe_superior_id != None:
                self.parent_id = self.department_id.parent_id.manager_id
            else:
                self.parent_id = None

    # tomar datos del usuario y escribirlos en empleado
    def _sync_user(self, user):
        return dict(
        )

    # tomar datos de la compañía y escribirlos en empleado
    @api.onchange('address_id')
    def _onchange_address(self):
        self.work_phone = self.address_id.phone
        pass

    @api.model
    def create(self, values):
        creado = super(HrEmployeeUpdated, self).create(values)
        if values['user_id']:
            user = self.user_id
            user.write({'name': self.name})
            user.write({'first_name': self.first_name, 'middle_name':self.middle_name})
            user.write({'last_name': self.last_name, 'second_last_name':self.second_last_name})
            partner = self.user_id.partner_id
            partner.write({'customer': False, 'supplier':True, 'employee': True})
        return creado

    @api.multi
    def write(self, values):
        actualizado = super(HrEmployeeUpdated, self).write(values) # bool
        
        employee = self.env['hr.employee'].browse(self.id)

        if values.get('department_id'):
            department = self.env['hr.department'].browse(values.get('department_id'))

            jefe_inmediato_id = department.manager_id.id
            if (jefe_inmediato_id != None) and (jefe_inmediato_id != employee.id):
                employee.write({'parent_id': jefe_inmediato_id})
            else:
                jefe_superior_id = department.parent_id.manager_id.id
                if jefe_superior_id != None:
                    employee.write({'parent_id': jefe_superior_id})
                else:
                    employee.write({'parent_id': None})
        return actualizado

# clase creada por alltic que actualiza responsables con cambio de jefe
class DepartmentResponsable(models.Model):
    _inherit = 'hr.department'

    @api.multi
    @api.onchange('manager_id')
    def _onchange_manager_id(self):
        # _logger.debug('***************')
        old_manager_obj = self._origin.manager_id # hr_employee
        new_manager_obj = self.manager_id # hr_employee

        # 0. reiniciando jefes involucrados
        old_manager_obj.write({'parent_id': None})
        new_manager_obj.write({'parent_id': None})

        # _logger.debug('0. nuevo jefe %s', new_manager_obj)
        # _logger.debug('0. antiguo jefe %s', old_manager_obj)

        # 1. actualizando antiguo jefe
        old_manager_obj.write({'parent_id': new_manager_obj.id})

        # _logger.debug('1. antiguo jefe %s', old_manager_obj)
        # _logger.debug('1. jefe antiguo jefe %s', old_manager_obj.parent_id)

        # 2. actualizando nuevo jefe
        if self.parent_id:
            new_parent = self.parent_id.manager_id
            new_manager_obj.write({'parent_id': new_parent.id})

        # _logger.debug('2. nuevo jefe %s', new_manager_obj)
        # _logger.debug('2. jefe nuevo jefe %s', new_manager_obj.parent_id)

        # 3. actualizando subordinados
        employees = self.env['hr.employee'].search([['parent_id', '=', old_manager_obj.id]])
        for e in employees:
            e.parent_id = new_manager_obj.id

        # _logger.debug('***************')
