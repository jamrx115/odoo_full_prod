# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, tools
from odoo.exceptions import UserError
import logging
import pytz
import re

_logger = logging.getLogger(__name__)
# _logger.debug('abc')

# Personalización de tareas de proyectos
class TaskCustom(models.Model):
	_inherit = "project.task"

	# override
	@api.depends('stage_id', 'timesheet_ids.unit_amount', 'planned_hours', 'child_ids.stage_id',
				 'child_ids.planned_hours', 'child_ids.effective_hours', 'child_ids.children_hours', 
				 'child_ids.timesheet_ids.unit_amount')
	def _hours_get(self):
		for task in self.sorted(key='id', reverse=True):
			children_hours = 0
			for child_task in task.child_ids:
				children_hours += child_task.effective_hours + child_task.children_hours

			task.children_hours = children_hours
			task.effective_hours = sum(task.sudo().timesheet_ids.mapped('unit_amount'))
			task.remaining_hours = task.planned_hours - task.effective_hours - task.children_hours
			task.total_hours = max(task.planned_hours, task.effective_hours)
			task.total_hours_spent = task.effective_hours + task.children_hours
			task.delay_hours = max(-task.remaining_hours, 0.0)

			if task.planned_hours > 0.0:
				task.progress = round(100.0 * (task.effective_hours + task.children_hours) / task.planned_hours, 2)
			else:
				task.progress = 0.0
