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
#_logger.debug('var %s', var)

# Herencia para mostrar si un empleado es miembro activo de comités SGSST
class CustomSstEmployee(models.Model):
	_inherit = 'hr.employee'

	current_sstcommittee = fields.Char(string="Actual comité SST", compute='_compute_sstcommittee')

	@api.multi
	def _compute_sstcommittee(self):
		for employee in self:
			active_applicant = self.env['custom.committee.applicant'].search(
				['&', ('employee_id', '=', employee.id), ('state', '=', 'activo')])
			if active_applicant:
				type_comm_value = dict(active_applicant.fields_get(allfields=['type_comm'])['type_comm']['selection'])[active_applicant.type_comm]
				type_brig_key = active_applicant.type_brig
				type_brig_value = ''
				if type_brig_key:
					type_brig_value = dict(active_applicant.fields_get(allfields=['type_brig'])['type_brig']['selection'])[active_applicant.type_brig]
				current_sstcommittee = type_comm_value + " - " + type_brig_value if type_brig_key else type_comm_value
				employee.current_sstcommittee = current_sstcommittee
