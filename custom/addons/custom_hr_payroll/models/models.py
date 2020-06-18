# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.addons.resource.models.resource import to_naive_utc, to_naive_user_tz, to_tz

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from datetime import time as datetime_time

import logging
import calendar
import babel
import time
import pytz
import re

_logger = logging.getLogger(__name__)
# _logger.debug('val %s', val)

# clase creada para agregar nuevos campos para reglas salariales
class PayslipWorkedDaysUpdated(models.Model):
    _inherit = 'hr.payslip.worked_days'

    number_of_days_calendar = fields.Float(string='Días Calendario')
    distance_from_holiday = fields.Integer(string='Distancia al inicio de la ausencia')
    holiday_id = fields.Integer(string='Código de la ausencia')

# clase creada por alltic que personaliza reglas salariales
class WorkedDaysLineUpdated(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        _logger.debug('')
        _logger.debug('***************')
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            # ******* (adapted) define day_from and day_to
            day_from_payslip = datetime.combine(fields.Date.from_string(date_from), datetime_time.min)
            day_to_payslip = datetime.combine(fields.Date.from_string(date_to), datetime_time.max)          
            
            day_from_contract = datetime.combine(fields.Date.from_string(contract.date_start), datetime_time.min)
            day_to_contract = datetime.combine(fields.Date.from_string(contract.date_end), datetime_time.max) if contract.date_end else False            
            
            day_from = day_from_contract if day_from_contract > day_from_payslip else day_from_payslip
            if day_to_contract:
                day_to = day_to_contract if day_to_contract < day_to_payslip else day_to_payslip
            else:
                day_to = day_to_payslip

            # compute LEAVE DAYS total (verified :: the dates are in UTC-0)
            leaves = {}
            day_leave_intervals = contract.employee_id.iter_leaves(day_from, day_to, calendar=contract.resource_calendar_id)
            public_holidays_count = 0
            
            for day_intervals in day_leave_intervals:                

                for interval in day_intervals:
                    holiday = interval[2]['leaves'].holiday_id # type :: hr.holidays
                    public_holiday = self.env['hr.holidays.public.line'].search([('date', '=', interval[0].date())]).date
                    weekday = True if ((interval[0].weekday() == 5) or (interval[0].weekday() == 6)) else False

                    aux_df_utczero = fields.Datetime.from_string(holiday.date_from)
                    aux_df_utc_user = to_naive_user_tz(aux_df_utczero, self.env.user)
                    ausencia_date_from = datetime.combine(aux_df_utc_user.date(), aux_df_utc_user.time())

                    # diccionario datos
                    current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                        'name': holiday.holiday_status_id.name or _('Global Leaves'),
                        'sequence': 5,
                        'code': holiday.holiday_status_id.code or 'GLOBAL',
                        'number_of_days': 0.0,
                        'number_of_hours': 0.0,
                        'contract_id': contract.id,

                        'number_of_days_calendar': 0.0,
                        'holiday_id': holiday.id,
                        'distance_from_holiday': (ausencia_date_from - day_from).days,
                    })
                    leave_time = (interval[1] - interval[0]).seconds / 3600
                    work_hours = contract.employee_id.get_day_work_hours_count(interval[0].date(), calendar=contract.resource_calendar_id)
                    # TIEMPO HABIL
                    if (not weekday and not public_holiday):
                        if work_hours:
                            current_leave_struct['number_of_hours'] += leave_time
                            current_leave_struct['number_of_days'] += round(leave_time / work_hours,2)
                    # TIEMPO CALENDARIO
                    if work_hours:
                        current_leave_struct['number_of_days_calendar'] += round(leave_time / work_hours,2)

            # compute worked days lun-vie (tiempo trabajado)
            work_data_ww = contract.employee_id.with_context(no_tz_convert=True).get_work_days_data_withoutweekday(day_from, day_to, calendar=contract.resource_calendar_id)

            work_data_complete = contract.employee_id.with_context(no_tz_convert=True).get_work_days_data_complete(day_from, day_to, calendar=contract.resource_calendar_id)
            sum_leaves_calendar_days = contract.employee_id.get_leaves_day_count(day_from, day_to, calendar=contract.resource_calendar_id)
            
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data_ww['days'],
                'number_of_hours': work_data_ww['hours'],
                'contract_id': contract.id,

                'number_of_days_calendar': (work_data_complete['days']-sum_leaves_calendar_days),
                'holiday_id': None,
                'distance_from_holiday': 0,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res 
