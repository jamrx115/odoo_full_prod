# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta, time
from odoo.addons.resource.models.resource import to_naive_utc, to_naive_user_tz, to_tz
from odoo import fields, models, api, tools
from odoo.exceptions import UserError
import logging
import pytz
import math
import re

_logger = logging.getLogger(__name__)

# Personalización de partes de horas
class AccountAnalyticLineNew(models.Model):
	_inherit = "account.analytic.line"

	def _default_datefrom(self):
		today_utc  = datetime.now() # utc cero
		today_user = to_naive_user_tz(today_utc, self.env.user)
		zero_user = datetime.combine(today_user.date(), time())
		zero_utc = to_naive_utc(zero_user, self.env.user)
		return zero_utc

	# date ya no se usa
	date_from = fields.Datetime('Fecha desde', required=True, index=True, default=_default_datefrom)
	date_to = fields.Datetime('Fecha fin', required=True, index=True)
	state = fields.Selection([
        ('enviado', 'Esperando revisión nómina'),
        ('aprobado', 'Aprobado nómina')], 
        string='Estado', default='enviado')
	stage_id = fields.Many2one(related="task_id.stage_id", string="Etapa", readonly=True)
	progress_min = fields.Float(related="stage_id.progress_min", string='Progreso Mínimo (%)', readonly=True)
	progress_max = fields.Float(related="stage_id.progress_max", string='Progreso Máximo (%)', readonly=True)
	current_progress = fields.Float(related="task_id.current_progress", string='Progreso general de la tarea (%)')

	_sql_constraints = [
        ('date_check', "CHECK ((date_from < date_to))", "La fecha inicial debe ser anterior a la fecha final."),
    ]

	def _get_number_of_hours(self, date_from, date_to, user_id):
		from_dt = fields.Datetime.from_string(date_from)
		to_dt = fields.Datetime.from_string(date_to)
		time_delta = to_dt - from_dt
		return (time_delta.total_seconds() / 3600)

	# onchange
	@api.onchange('date_from')
	def _onchange_date_from(self):
		date_from = self.date_from
		date_to = self.date_to

		# No date_to set so far: automatically compute one 1 hours later
		if date_from and not date_to:
			date_to_with_delta = fields.Datetime.from_string(date_from) + timedelta(hours=1)
			self.date_to = str(date_to_with_delta)

		# Compute and update the number of hours
		if (date_to and date_from) and (date_from <= date_to):
			self.unit_amount = self._get_number_of_hours(date_from, date_to, self.user_id.id)
		else:
			self.unit_amount = 0

	@api.onchange('date_to')
	def _onchange_date_to(self):
		date_from = self.date_from
		date_to = self.date_to

		# Compute and update the number of hours
		if (date_to and date_from) and (date_from <= date_to):
			self.unit_amount = self._get_number_of_hours(date_from, date_to, self.user_id.id)
		else:
			self.unit_amount = 0

	@api.multi
	def write(self, vals):
		for obj in self:
			old_progress = obj.current_progress
			lim_min = obj.progress_min
			lim_max = obj.progress_max

			possible_new_progress = vals.get('current_progress')
			if possible_new_progress:
				if ((possible_new_progress < lim_min) or (possible_new_progress > lim_max)):
					raise UserError(('Nuevo progreso no válido, debe estar entre %s y %s. Puede regresar a %s.') % (lim_min, lim_max, old_progress))

		return super(AccountAnalyticLineNew, self).write(vals)
