# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
import pytz # personalización Alltic

class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    def _get_number_of_days(self, date_from, date_to, employee_id):
        if (self.holiday_status_id.exclude_public_holidays or
                not self.holiday_status_id):
            obj = self.with_context(
                employee_id=employee_id,
                exclude_public_holidays=True,
            )
        else:
            obj = self
        return super(HrHolidays, obj)._get_number_of_days(
            date_from, date_to, employee_id,
        )

    @api.onchange('employee_id', 'holiday_status_id')
    def _onchange_data_hr_holidays_public(self):
        """Trigger the number of days computation also when you change the
        employee or the leave type.
        """
        self._onchange_date_to()

# personalización Alltic
class HrHolidaysUpdate(models.Model):
    _inherit = 'hr.holidays'

    # return holidays public IN DICT
    def get_publicholidays_ids(self, date_from, date_to, country_emp_id):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        date_from_tz_user = user_tz.fromutc(date_from) # tz user
        date_to_tz_user = user_tz.fromutc(date_to)  # tz user
        holidays_ids = None

        if date_from_tz_user.year == date_to_tz_user.year:
            holidays_ids = self.env['hr.holidays.public.line'].search(
                ['&', '&', ('date', '>=', date_from_tz_user), ('date', '<=', date_to_tz_user),
                ('year_id', '=', self.env['hr.holidays.public'].search(['&', ('year', '=', date_from_tz_user.year),
                                                                       ('country_id', '=', country_emp_id)]).id)])
        else:
            holidays_ids1 = self.env['hr.holidays.public.line'].search(
                ['&', '&', ('date', '>=', date_from_tz_user),
                ('date', '<=', datetime.strptime(str(date_from_tz_user.year) + '-12-31', '%Y-%m-%d')),
                ('year_id', '=', self.env['hr.holidays.public'].search(['&', ('year', '=', date_from_tz_user.year),
                                                                       ('country_id', '=', country_emp_id)]).id)])
            holidays_ids2 = self.env['hr.holidays.public.line'].search(
                ['&', '&', ('date', '>=', datetime.strptime(str(date_to_tz_user.year) + '-01-01', '%Y-%m-%d')),
                ('date', '<=', date_to_tz_user),
                ('year_id', '=', self.env['hr.holidays.public'].search(['&', ('year', '=', date_to_tz_user.year),
                                                                        ('country_id', '=', country_emp_id)]).id)])
            holidays_ids = holidays_ids1 | holidays_ids2

        return holidays_ids
