# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP


from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

import logging
import calendar
import pytz
import re

_logger = logging.getLogger(__name__)

# Clase que crea campos o metodos
class CustomJob(models.Model):
	_inherit = 'hr.job'

	x_usual_posture = fields.Char(string='Postura habitual', groups="hr_recruitment.group_hr_recruitment_manager")
	job_analisys_bool = fields.Boolean(string='Existen analisis de puesto de trabajo', groups="hr_recruitment.group_hr_recruitment_manager")
	elem_str = fields.Text('Elementos de proteccion personal')
	tools_equipment = fields.Text('Herramientas y equipos')
