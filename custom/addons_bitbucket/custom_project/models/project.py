# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, tools
from odoo.exceptions import UserError
import logging
import pytz
import re

_logger = logging.getLogger(__name__)

# Personalización de tareas de proyectos
class TaskCustom(models.Model):
	_inherit = "project.task"

	label_task = fields.Char(related='project_id.label_tasks', store=True)
