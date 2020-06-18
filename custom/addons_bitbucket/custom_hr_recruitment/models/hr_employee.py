# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import fields, models, api, tools
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
import pytz
import re

_logger = logging.getLogger(__name__)

class EmployeePreviousTravel(models.Model):
	_name = "employee.previous.travel"
	_description = "Viajes laborales"
	_rec_name = "from_date"
	_order = "from_date"

	from_date = fields.Date(string='Fecha inicial', required=True)
	to_date = fields.Date(string='Fecha final', required=True)
	country_id = fields.Many2one('res.country', 'País', ondelete='cascade')
	city_id = fields.Many2one('res.city', 'Ciudad', ondelete='cascade')
	reason = fields.Char('Motivo', required=True)
	active = fields.Boolean(string='Activo', default=True)
	employee_id = fields.Many2one('hr.employee', 'Empleado', ondelete='cascade')
	partner_id = fields.Many2one('res.partner', 'Hotel', domain="[('supplier', '=', True)]")
	daily_value = fields.Float(string='Viáticos diarios')

	@api.model
	def create(self, vals):
		if (self._context.get('active_model') == 'hr.employee' and self._context.get('active_id')):
			vals.update({'employee_id': self._context.get('active_id')})
		return super(EmployeePreviousTravel, self).create(vals)

	@api.onchange('from_date', 'to_date')
	def onchange_date(self):
		if self.to_date and datetime.strptime(self.to_date, DEFAULT_SERVER_DATE_FORMAT) >= datetime.today():
			warning = {'title': _('User Alert !'), 'message': _('To date must be less than today !')}
			self.to_date = False
			return {'warning': warning}
		if self.from_date and self.to_date and self.from_date > self.to_date:
			warning = {'title': _('User Alert !'), 'message': _('To Date %s must be greater than From Date %s !') % (self.to_date, self.from_date)}
			self.to_date = False
			return {'warning': warning}

	@api.multi
	@api.onchange('country_id')
	def _onchange_country_id(self):
		if self.country_id:
			return {'domain': {'city_id': [('country_id', '=', self.country_id.id)]}}
		else:
			return {'domain': {'city_id': []}}

class EmployeeLanguage(models.Model):
	_name = "employee.language"
	_description = "Idioma empleado"
	_rec_name = "language"
	_order = "id desc"

	language = fields.Char('Idioma', required=True)
	read_lang = fields.Selection(
		[('Excelente', 'Excelente'), ('Bien', 'Bien'), ('Regular', 'Regular')],
		string='Lee')
	write_lang = fields.Selection(
		[('Excelente', 'Excelente'), ('Bien', 'Bien'), ('Regular', 'Regular')],
		string='Escribe')
	speak_lang = fields.Selection(
		[('Excelente', 'Excelente'), ('Bien', 'Bien'), ('Regular', 'Regular')],
		string='Habla')
	active = fields.Boolean(string='Activo', default=True)
	employee_id = fields.Many2one('hr.employee', 'Empleado', ondelete='cascade')
	mother_tongue = fields.Boolean('Lengua materna')

	@api.constrains('mother_tongue')
	def _check_mother_tongue(self):
		self.ensure_one()
		if self.mother_tongue and self.employee_id:
			language_rec = self.search([
				('employee_id', '=', self.employee_id.id),
				('mother_tongue', '=', True), ('id', '!=', self.id)],
				limit=1)
			if language_rec:
				raise ValidationError(_("If you want to set '%s' as a mother tongue, first you have to uncheck mother tongue in '%s' language.") % 
					(self.language, language_rec.language))

	@api.model
	def create(self, vals):
		if self._context.get('active_model') == 'hr.employee' and self._context.get('active_id'):
			vals.update({'employee_id': self._context.get('active_id')})
		return super(EmployeeLanguage, self).create(vals)

class EmployeeRelative(models.Model):
	_name = 'employee.relative'
	_description = "Familiares empleado"
	_rec_name = 'name'

	relative_type = fields.Selection([
		('Padre', 'Padre'),
		('Madre', 'Madre'),
		('Esposo', 'Esposo'),
		('Esposa', 'Esposa'),
		('Hermano', 'Hermano'),
		('Hermana', 'Hermana')],
		string='Parentesco', required=True)
	name = fields.Char(string='Nombre completo', required=True)
	birthday = fields.Date(string='Fecha de nacimiento')
	occupation = fields.Char(string='Ocupación')
	gender = fields.Selection(
		[('Masculino', 'Masculino'),
		('Femenino', 'Femenino')],
		string='Género', required=False)
	active = fields.Boolean(string='Activo', default=True)
	employee_id = fields.Many2one('hr.employee', 'Empleado', ondelete='cascade')
	identification_type = fields.Selection([
		('12', 'Tarjeta de identidad'),
		('13', 'Cédula de ciudadanía'),
		('21', 'Tarjeta de extranjería'),
		('22', 'Cédula de extranjería') ],
		string='Tipo identificación')
	identification_id = fields.Char(string='Identificación No')
	country_id = fields.Many2one('res.country', 'País', ondelete='cascade')
	city_id = fields.Many2one('res.city', 'Ciudad', ondelete='cascade')
	phone = fields.Char(string='Teléfono')
	address = fields.Char(string='Dirección')
	email = fields.Char(string='Correo Electrónico')

	@api.onchange('birthday')
	def onchange_birthday(self):
		if self.birthday and datetime.strptime(self.birthday, DEFAULT_SERVER_DATE_FORMAT) >= datetime.today():
			warning = {'title': _('User Alert !'), 'message': _('Date of Birth must be less than today!')}
			self.birthday = False
			return {'warning': warning}

	@api.onchange('relative_type')
	def onchange_relative_type(self):
		if self.relative_type:
			if self.relative_type in ('Padre', 'Esposo', 'Hermano'):
				self.gender = 'Masculino'
			elif self.relative_type in ('Madre', 'Esposa', 'Hermana'):
				self.gender = 'Femenino'
			else:
				self.gender = ''

	@api.multi
	@api.onchange('country_id')
	def _onchange_country_id(self):
		if self.country_id:
			return {'domain': {'city_id': [('country_id', '=', self.country_id.id)]}}
		else:
			return {'domain': {'city_id': []}}

	@api.model
	def create(self, vals):
		if (self._context.get('active_model') == 'hr.employee' and
			self._context.get('active_id')):
			vals.update({'employee_id': self._context.get('active_id')})
		return super(EmployeeRelative, self).create(vals)

class EmployeeChildren(models.Model):
	_name = 'employee.children'
	_description = "Hijos empleado"
	_rec_name = 'name'

	relative_type = fields.Selection([
		('Hijo', 'Hijo'),
		('Hija', 'Hija')],
		string='Parentesco', required=True)
	name = fields.Char(string='Nombre completo', required=True)
	birthday = fields.Date(string='Fecha de nacimiento')
	gender = fields.Selection(
		[('Masculino', 'Masculino'),
		('Femenino', 'Femenino')],
		string='Género', required=False)
	active = fields.Boolean(string='Activo', default=True)
	employee_id = fields.Many2one('hr.employee', 'Empleado', ondelete='cascade')
	identification_type = fields.Selection([
		('12', 'Tarjeta de identidad'),
		('13', 'Cédula de ciudadanía'),
		('21', 'Tarjeta de extranjería'),
		('22', 'Cédula de extranjería') ],
		string='Tipo identificación')
	identification_id = fields.Char(string='Identificación No')
	country_id = fields.Many2one('res.country', 'País', ondelete='cascade')
	city_id = fields.Many2one('res.city', 'Ciudad', ondelete='cascade')
	phone = fields.Char(string='Teléfono')

	@api.onchange('birthday')
	def onchange_birthday(self):
		if self.birthday and datetime.strptime(self.birthday, DEFAULT_SERVER_DATE_FORMAT) >= datetime.today():
			warning = {'title': _('User Alert !'), 'message': _('Date of Birth must be less than today!')}
			self.birthday = False
			return {'warning': warning}

	@api.multi
	@api.onchange('country_id')
	def _onchange_country_id(self):
		if self.country_id:
			return {'domain': {'city_id': [('country_id', '=', self.country_id.id)]}}
		else:
			return {'domain': {'city_id': []}}

	@api.model
	def create(self, vals):
		if (self._context.get('active_model') == 'hr.employee' and
			self._context.get('active_id')):
			vals.update({'employee_id': self._context.get('active_id')})
		return super(EmployeeChildren, self).create(vals)

class Employee(models.Model):
	_inherit = "hr.employee"

	@api.depends('prev_travel_ids')
	def _compute_no_of_prev_travel(self):
		for rec in self:
			rec.no_of_prev_travel = len(rec.prev_travel_ids.ids)

	@api.depends('lang_ids')
	def _compute_no_of_lang(self):
		for rec in self:
			rec.no_of_lang = len(rec.lang_ids.ids)

	@api.depends('relative_ids')
	def _compute_no_of_relative(self):
		for rec in self:
			rec.no_of_relative = len(rec.relative_ids.ids)

	@api.depends('children_ids')
	def _compute_no_of_children(self):
		for rec in self:
			rec.children = len(rec.children_ids.ids)

	prev_travel_ids = fields.One2many('employee.previous.travel', 'employee_id', 'Viajes laborales.')
	no_of_prev_travel = fields.Integer('Num de viajes', compute='_compute_no_of_prev_travel', readonly=True)
	lang_ids = fields.One2many('employee.language', 'employee_id', 'Idiomas.')
	no_of_lang = fields.Integer('Num de idiomas', compute='_compute_no_of_lang', readonly=True)
	relative_ids = fields.One2many('employee.relative', 'employee_id', 'Familiares.')
	no_of_relative = fields.Integer('No of Relative', compute='_compute_no_of_relative', readonly=True)
	children_ids = fields.One2many('employee.children', 'employee_id', 'Hijos.')
	children = fields.Integer(string='Num de hijos', compute='_compute_no_of_children', readonly=True)
