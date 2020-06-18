# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)
# _logger.debug('day_intervals %s', day_intervals)

class ResourceMixinUpdated(models.AbstractModel):
    _inherit = "resource.mixin"

    # días entre semana con festivos
    def get_work_days_data(self, from_datetime, to_datetime, calendar=None):
        days_count = 0.0
        total_work_time = timedelta()
        calendar = calendar or self.resource_calendar_id
        calendar = calendar.with_context(no_tz_convert=self.env.context.get('no_tz_convert', False))
        for day_intervals in calendar._iter_work_intervals(
                from_datetime, to_datetime, self.resource_id.id,
                compute_leaves=True):
            # theoric_hours  :: horas totales trabajables en el día
            theoric_hours = self.get_day_work_hours_count(day_intervals[0][0].date(), calendar=calendar)
            # work_time      :: horas del intervalo
            if (day_intervals[0][0].weekday() == 5) and self.company_id.recognize_saturday:
                work_time = timedelta(seconds=0)
            elif (day_intervals[0][0].weekday() == 6) and self.company_id.recognize_sunday:
                work_time = timedelta(seconds=0)
            else:
                work_time = sum((interval[1] - interval[0] for interval in day_intervals), timedelta())
            # total_work_time :: horas acumuladas
            total_work_time += work_time
            if theoric_hours:
                days_count += round((work_time.total_seconds() / 3600 / theoric_hours), 2)
        return {
            'days': days_count,
            'hours': total_work_time.total_seconds() / 3600,
        }

    # días entre semana sin festivos
    def get_work_days_data_withoutweekday(self, from_datetime, to_datetime, calendar=None):
        days_count = 0.0
        total_work_time = timedelta()
        calendar = calendar or self.resource_calendar_id
        calendar = calendar.with_context(no_tz_convert=self.env.context.get('no_tz_convert', False))
        for day_intervals in calendar._iter_work_intervals(
                from_datetime, to_datetime, self.resource_id.id,
                compute_leaves=True):
            # theoric_hours  :: horas totales trabajables en el día       
            theoric_hours = self.get_day_work_hours_count(day_intervals[0][0].date(), calendar=calendar)
            # public holiday
            public_holiday = self.env['hr.holidays.public.line'].search([('date', '=', day_intervals[0][0].date())]).date
            # work_time      :: horas del intervalo
            if (day_intervals[0][0].weekday() == 5) and self.company_id.recognize_saturday:
                work_time = timedelta(seconds=0)
            elif (day_intervals[0][0].weekday() == 6) and self.company_id.recognize_sunday:
                work_time = timedelta(seconds=0)
            elif public_holiday:
                work_time = timedelta(seconds=0)
            else:
                work_time = sum((interval[1] - interval[0] for interval in day_intervals), timedelta())
            # total_work_time :: horas acumuladas
            total_work_time += work_time
            if theoric_hours:
                days_count += round((work_time.total_seconds() / 3600 / theoric_hours), 2)
        return {
            'days': days_count,
            'hours': total_work_time.total_seconds() / 3600,
        }

    # días calendario
    def get_work_days_data_complete(self, from_datetime, to_datetime, calendar=None):
        days_count = 0.0
        total_work_time = timedelta()
        calendar = calendar or self.resource_calendar_id
        calendar = calendar.with_context(no_tz_convert=self.env.context.get('no_tz_convert', False))
        for day_intervals in calendar._iter_work_intervals(
                from_datetime, to_datetime, self.resource_id.id,
                compute_leaves=False):
            theoric_hours = self.get_day_work_hours_count(day_intervals[0][0].date(), calendar=calendar)
            work_time = sum((interval[1] - interval[0] for interval in day_intervals), timedelta())
            total_work_time += work_time
            if theoric_hours:
                days_count += round((work_time.total_seconds() / 3600 / theoric_hours), 2)
        return {
            'days': days_count,
            'hours': total_work_time.total_seconds() / 3600,
        }

    # se modifica sólo por redondeo
    def get_leaves_day_count(self, from_datetime, to_datetime, calendar=None):
        days_count = 0.0
        calendar = calendar or self.resource_calendar_id
        for day_intervals in calendar._iter_leave_intervals(from_datetime, to_datetime, self.resource_id.id):
            theoric_hours = self.get_day_work_hours_count(day_intervals[0][0].date(), calendar=calendar)
            leave_time = sum((interval[1] - interval[0] for interval in day_intervals), timedelta())
            if theoric_hours:
                days_count += round((leave_time.total_seconds() / 3600 / theoric_hours), 2)
        return days_count
