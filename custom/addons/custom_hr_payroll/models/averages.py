# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.addons.resource.models.resource import to_naive_utc, to_naive_user_tz, to_tz

from datetime import datetime, timedelta
from datetime import time as datetime_time
from dateutil.relativedelta import relativedelta

import logging
import calendar
import babel
import pytz
import re

_logger = logging.getLogger(__name__)

# clase creada para agregar nuevos campos para reglas salariales
class SalaryRuleAverages(models.Model):
	_inherit = 'hr.payslip'

	# auxiliar de conteo
	def auxiliar_for_sum(self, date_from_str, date_to_str, tiempo):
		# _logger.debug('++++++++++++++++')
		# _logger.debug('tiempo %s', tiempo)
		date_from = fields.Datetime.from_string(date_from_str).date()
		date_to   = fields.Datetime.from_string(date_to_str).date()
		sub = 0.0
		if tiempo == 'DIAS':
			sub = ((date_to-date_from).days)+1
		elif tiempo == 'MESES_ROUND_2D':
			delta = relativedelta(date_to, date_from)
			sub = delta.months + round((delta.days * 1.0 / 30.0),2)
		elif tiempo == 'MESES_EXACTOS_ROUND':
			if date_from.day <= 15:
				date_from = datetime(year=date_from.year, month=date_from.month, day=15)
			else:
				date_from = datetime(year=date_from.year, month=date_from.month, day=calendar.monthrange(date_from.year, date_from.month)[1])

			delta = relativedelta(date_to, date_from)
			dias = delta.days

			ult_dia_mes = calendar.monthrange(date_to.year, date_to.month)[1]
			if ult_dia_mes == 28:
				dias = dias + 2
			elif ult_dia_mes == 29:
				dias = dias + 1
			elif ult_dia_mes == 31:
				dias = dias - 1
			else:
				dias = dias

			if dias <= 15:
				if dias <= 0:
					sub = delta.months
				else:
					sub = delta.months + 0.5
			else:
				sub = delta.months + 1.0
		# default :: 'MESES' :: número de meses cubiertos
		else:
			sub = ((date_to.month-date_from.month)%12)+1
		# _logger.debug('++++++++++++++++')
		return sub

	# time_p = 'DIAS', 'MESES' (default), 'MESES_ROUND_Q'
	# rule = 'PRIMA'
	@api.multi
	def run_payslips_bytime(self, employee_id, date_from_payslip, date_to_payslip, time_p, rule):
		# _logger.debug('***************')
		tipo_novedad_contrato_vinculacion = self.env['custom.tipo.novedad.contrato'].search([('name', 'like', 'Vinculación%')])
		employee = self.env['hr.employee'].browse(employee_id)  # tipo hr_employee
		date_from_payslip = fields.Datetime.from_string(date_from_payslip)  # tipo datetime
		date_to_payslip = fields.Datetime.from_string(date_to_payslip)  # tipo datetime
		aux_year = date_from_payslip.year
		aux_meses = 0
		result = 0
		dias = 0

		if rule == 'PRIMA':
			aux_cmeses = 0
			if date_from_payslip.month == 1:
				meses = [mn for mn in range(1, date_to_payslip.month + 1)]
			else:
				meses = [mn for mn in range(date_from_payslip.month, 13)]
		if meses:
			aux_meses = meses[0]

		# _logger.debug('time_p %s', time_p)

		if time_p.startswith('MESES') and rule != 'PRIMA':
			result = aux_cmeses
		else:
			for mes in meses:
				date_from_mes = datetime(year=aux_year, month=mes, day=1)  # tipo datetime
				date_to_mes   = datetime(year=aux_year, month=mes, day=calendar.monthrange(aux_year, mes)[1])  # tipo datetime

				payslip_ids = self.env['hr.payslip'].search(
					['&', '&', '&', ('date_from', '>=', date_from_mes), ('date_to', '<=', date_to_mes),
					('employee_id', '=', employee.id),
					('state', '=', 'done')])

				for nomina in payslip_ids:
					contract = self.env['hr.contract'].search([('id', '=', nomina.contract_id.id)])
					date_from_p = fields.Datetime.from_string(nomina.date_from)
					date_to_p = fields.Datetime.from_string(nomina.date_to)
					# _logger.debug('fechas %s - %s salario %s', nomina.date_from, nomina.date_to, contract.wage)

					if contract:
						salario = contract.wage
						contract_start = fields.Datetime.from_string(contract.date_start)  # tipo datetime
						contract_end = False
						if contract.date_end:
							contract_end = fields.Datetime.from_string(contract.date_end)  # tipo datetime

						if contract_start < date_from_p:
							if contract_end:
								if date_to_p < contract_end:
									dias = ((date_to_p - date_from_p).days) + 1
								else:
									dias = ((contract_end - date_from_p).days) + 1
							else:
								dias = ((date_to_p - date_from_p).days) + 1
						else:
							if contract_end:
								if date_to_p < contract_end:
									dias = ((date_to_p - contract_start).days) + 1
								else:
									dias = ((contract_end - contract_start).days) + 1
							else:
								dias = ((date_to_p - contract_start).days) + 1
						# correccion dias para redondear a 30
						if date_from_p.month == 2:
							if date_to_p.day == 28:
								dias += 2
							if date_to_p.day == 29:
								dias += 1
						if date_to_p.day == 31 and (dias >= 16):
							dias -= 1

						# calculando resutado
						if time_p == 'WAGE':
							result += ((salario / 30) * dias)
							# _logger.debug('W')
							# _logger.debug('fechas %s - %s salario %s', nomina.date_from, nomina.date_to, ((salario / 30) * dias))
						else:
							result += dias
							# _logger.debug('T')
							# _logger.debug('fechas %s - %s valor dias %s', nomina.date_from, nomina.date_to, dias)

				aux_meses +=1
				if aux_meses%13 == 0:
					aux_year = aux_year + 1

			# ajuste en caso de time_p = 'MESES_ROUND_2D', rule = 'PRIMA'
			if time_p == 'MESES_ROUND_2D' and rule == 'PRIMA':
				result = result / 30
		# _logger.debug('***************')
		return result

	# rule = 'PRIMA'
	# code = 'DIASVAC', 'AUXTRANSP', 'COMISIONES', etc
	@api.multi
	def run_payslips_bycode(self, employee_id, date_from_payslip, date_to_payslip, rule, code):
		# _logger.debug('***************')
		tipo_novedad_contrato_vinculacion = self.env['custom.tipo.novedad.contrato'].search([('name', 'like', 'Vinculación%')])
		employee = self.env['hr.employee'].browse(employee_id)  # tipo hr_employee
		date_from_payslip = fields.Datetime.from_string(date_from_payslip)  # tipo datetime
		date_to_payslip = fields.Datetime.from_string(date_to_payslip)  # tipo datetime

		if rule == 'PRIMA' or rule == 'PRIMALIQ':
			if date_to_payslip.month <= 6:
				date_from = datetime(year=date_from_payslip.year, month=1, day=1)  # tipo datetime
				date_to = datetime(year=date_to_payslip.year, month=6, day=30)  # tipo datetime
			else:
				date_from = datetime(year=date_from_payslip.year, month=7, day=1)  # tipo datetime
				date_to = datetime(year=date_to_payslip.year, month=12, day=31)  # tipo datetime
		else:
			date_from = datetime(year=date_from_payslip.year, month=1, day=1)  # tipo datetime
			date_to = datetime(year=date_to_payslip.year, month=12, day=31)  # tipo datetime

		# _logger.debug('date_from_bono %s', date_from)
		# _logger.debug('date_to_bono %s', date_to)
		# _logger.debug('')

		result = 0.0
		contract_ids = self.get_contract(employee, date_from, date_to)  # tipo [int]
		# _logger.debug('contract_ids %s', contract_ids)

		payslip_ids = []

		for contract_id in contract_ids:
			c = self.env['hr.contract'].browse(contract_id)
			# _logger.debug('fechas c %s a %s', c.date_start, c.date_end)
			payslip_aux = self.env['hr.payslip'].search(
				['&', '&', '&', ('date_from', '>=', date_from), ('date_to', '<=', date_to),
				('contract_id', '=', contract_id),
				('state', '=', 'done')], order='date_from asc').ids
			# _logger.debug('payslip_aux %s', payslip_aux)
			payslip_ids = payslip_aux + payslip_ids
			# _logger.debug('payslip_ids :: %s', payslip_ids)

		# _logger.debug('payslip_ids :: %s', payslip_ids)

		for payslip_id in payslip_ids:
			# _logger.debug('')
			payslip = self.env['hr.payslip'].browse(payslip_id)
			# _logger.debug('fechas %s - %s', payslip.date_from, payslip.date_to)
			for input_line in payslip.line_ids:
				# _logger.debug('code %s', code)
				if input_line.code == code:
					result += input_line.amount
					# _logger.debug('valor %s', input_line.amount)
					# _logger.debug('subtotal %s', result)

		return result

	# delta_time = '-1month', '+1month'
	# code = 'DIASVAC', 'AUXTRANSP', 'COMISIONES', etc
	@api.multi
	def get_totaldays_vac(self, contract_obj, date_from_payslip, holiday_id, distance_from_holiday):
		date_from = fields.Datetime.from_string(date_from_payslip).date()
		date_to = datetime(year=date_from.year, month=date_from.month, day=calendar.monthrange(date_from.year, date_from.month)[1]).date()
		result = 0.0
		holiday_obj = self.env['hr.holidays'].browse(holiday_id)
		return -holiday_obj.number_of_days_calendar
