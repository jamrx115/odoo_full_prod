# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from datetime import datetime, timedelta, time
import logging
import math

_logger = logging.getLogger(__name__)
# _logger.debug('---------------')
# _logger.debug('day_intervals 0 %s', day_intervals[0])
HOURS_PER_DAY = 8

class HolidaysCalendarDays(models.Model):
    _inherit = 'hr.holidays'

    number_of_days_calendar = fields.Float('Días Calendario')

    # obtiene la cantidad de días desde el horario sin tener en cuenta
    # fines de semana ni festivos, necesario para cálculos
    def _get_number_of_days_complete(self, date_from, date_to, employee_id):
        from_dt = fields.Datetime.from_string(date_from)
        to_dt = fields.Datetime.from_string(date_to)

        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            return employee.get_work_days_data_complete(from_dt, to_dt)['days']

        time_delta = to_dt - from_dt
        return math.ceil(time_delta.days + float(time_delta.seconds) / 86400)

    # escribe en base de datos el número de días calendario para cualquier ausencia
    def write_number_of_days_calendar(self, date_from_str, date_to_str, employee_id):
        calendar_days = self._get_number_of_days_complete(self.date_from, self.date_to, self.employee_id.id)
        if self.type == 'remove':
            calendar_days = -1 * calendar_days        
        self.write({'number_of_days_calendar': calendar_days})
