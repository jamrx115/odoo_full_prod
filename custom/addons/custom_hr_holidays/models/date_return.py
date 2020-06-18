# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from datetime import datetime, timedelta, time
from odoo.addons.resource.models.resource import to_naive_utc, to_naive_user_tz, to_tz
import logging

_logger = logging.getLogger(__name__)
# _logger.debug('---------------')
# _logger.debug('day_intervals 0 %s', day_intervals[0])
HOURS_PER_DAY = 8

class HolidaysDateReturn(models.Model):
    _inherit = 'hr.holidays'

    date_return = fields.Datetime('Fecha de regreso', readonly=True, index=True, copy=False)
    
    # retorna True si la fecha es festivo o fin de semana
    def is_special_day(self, date, employee_id):
        answer = False
        date_str = str(date.date())
        date_is_holiday = self.env['hr.holidays.public'].is_public_holiday(date_str, employee_id)
        if date_is_holiday or (date.weekday() == 5) or (date.weekday() == 6): answer = True
        return answer

    # calcula el día de regreso (se usa para ausencias de vacaciones
    # o cuando la ausencia termina en la última hora del horario del trabajador)
    def calculate_return_day(self, date_to_utczero, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        date_tz_user_complete = to_naive_user_tz(date_to_utczero, self.env.user)
        date_tz_user = datetime.combine(date_tz_user_complete.date(), date_tz_user_complete.time())

        day = date_tz_user+timedelta(days=1)
        control = self.is_special_day(day, employee_id)

        while (control):
            if day.weekday() == 5:
                day = day+timedelta(days=2)
            else:
                day = day+timedelta(days=1)
            control = self.is_special_day(day, employee_id)

        day = datetime.combine(day.date(), time())
        return_day_uctzero = employee.get_start_work_hour(day, employee.resource_calendar_id)
        # return_day_utcuser = to_naive_user_tz(return_day_uctzero, self.env.user)
        return return_day_uctzero

    # calcula la hora de regreso (se usa para las ausencias distintas a
    # vacaciones y cuando la ausencia no dura todo el día ni termina en
    # la hora final del turno del empleado)
    def calculate_return_hour(self, date_to_utczero, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        date_tz_user = to_naive_user_tz(date_to_utczero, self.env.user)

        date_to_utcuser_min = datetime.combine(date_tz_user.date(), time(hour=0, minute=0, second=0))
        date_to_utcuser_max = datetime.combine(date_tz_user.date(), time(hour=23, minute=59, second=59))

        date_to_utczero_min = to_naive_utc(date_to_utcuser_min, self.env.user)
        date_to_utczero_max = to_naive_utc(date_to_utcuser_max, self.env.user)

        calendar = employee.resource_calendar_id
        intervalos = calendar._schedule_days(1,date_to_utczero, employee.resource_id.id)
        intervalos_list = []
        
        for i in intervalos:
            intervalos_list.append([i[0],i[1]])
        for idx, val in enumerate(intervalos_list):
            # _logger.debug('=> intervalo %s', val)
            if date_to_utczero > val[0] and date_to_utczero <  val[1]:
                # return date_to_utczero + timedelta(seconds=1)
                return date_to_utczero
            elif date_to_utczero == val[1]:
                if val != intervalos_list[-1]:
                    return intervalos_list[idx+1][0]
            elif date_to_utczero == val[0]:
                return val[0]

    # cálculo principal de día u hora de regreso
    def write_return_day(self, date_to_str, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        if self.type == 'remove':
            date_to_utczero   = fields.Datetime.from_string(self.date_to)
            date_to_utcuser = to_naive_user_tz(date_to_utczero, self.env.user)

            date_to_utcuser_min = datetime.combine(date_to_utcuser.date(), time.min)
            date_to_utcuser_max = datetime.combine(date_to_utcuser.date(), time.max)

            date_to_utczero_min = to_naive_utc(date_to_utcuser_min, self.env.user)
            date_to_utczero_max = to_naive_utc(date_to_utcuser_max, self.env.user)

            lastday_hours_leave = employee.resource_calendar_id.get_work_hours_count(
                date_to_utczero_min, date_to_utczero, employee.resource_id.id, compute_leaves=False)

            lastday_hours_total = employee.resource_calendar_id.get_work_hours_count(
                date_to_utczero_min, date_to_utczero_max, employee.resource_id.id, compute_leaves=False)

            if (lastday_hours_leave < lastday_hours_total) and not (self.is_special_day(date_to_utcuser, employee_id)):
                date_return = self.calculate_return_hour(date_to_utczero, employee.id)
            else:
                date_return = self.calculate_return_day(date_to_utczero, employee.id)
            self.write({'date_return': date_return})
