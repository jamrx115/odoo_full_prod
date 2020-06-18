# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, time
from odoo.addons.resource.models.resource import to_naive_utc, to_naive_user_tz, to_tz
import logging

_logger = logging.getLogger(__name__)
# _logger.debug('---------------')
# _logger.debug('day_intervals 0 %s', day_intervals[0])
HOURS_PER_DAY = 8

class HolidaysEmails(models.Model):
    _inherit = 'hr.holidays'

    def send_email_confirm_state(self):
        template = self.env.ref('custom_hr_holidays.confirm_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    def send_email_validate_state(self):
        template = self.env.ref('custom_hr_holidays.approve_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    def send_email_validate1_state(self):
        template = self.env.ref('custom_hr_holidays.validate_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    def send_email_refuse_state(self):
        template = self.env.ref('custom_hr_holidays.refuse_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    def send_email_delay_state(self):
        template = self.env.ref('custom_hr_holidays.postponed_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

class HolidaysDefaultDates(models.Model):
    _inherit = 'hr.holidays'

    def _default_zero(self):
        today_utc  = datetime.now() # utc cero
        today_user = to_naive_user_tz(today_utc, self.env.user)
        zero_user = datetime.combine(today_user.date(), time())
        zero_utc = to_naive_utc(zero_user, self.env.user)
        return zero_utc

    def _default_final(self):
        today_utc   = datetime.now()# utc cero
        today_user  = to_naive_user_tz(today_utc, self.env.user)
        fnhour_user = datetime.combine(today_user.date(), time(hour=23, minute=59, second=59))
        fnhour_utc = to_naive_utc(fnhour_user, self.env.user)
        return fnhour_utc

    date_from = fields.Datetime('Fecha inicio', readonly=True, index=True, copy=False,
            states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'delay': [('readonly', False)]}, track_visibility='onchange',
            default=_default_zero)
    date_to = fields.Datetime('Fecha fin', readonly=True, copy=False,
            states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'delay': [('readonly', False)]}, track_visibility='onchange',
            default=_default_final)

#clase creada por alltic que modifica las ausencias
class HolidaysUpdated(models.Model):
    _inherit = 'hr.holidays'

    report_note = fields.Text('HR Comments', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'delay': [('readonly', False)]})

    def _check_admin_group(self):
        is_holiday_manager  = self.env['res.users'].has_group('hr_holidays.group_hr_holidays_manager')
        is_holiday_user     = self.env['res.users'].has_group('hr_holidays.group_hr_holidays_user')
        is_holiday_headarea = self.env['res.users'].has_group('custom_hr_holidays.group_custom_head_of_area')
        return is_holiday_manager or is_holiday_user or is_holiday_headarea

    def _check_state_access_right(self, vals):
        if vals.get('state') and vals['state'] not in ['draft', 'confirm', 'cancel'] and not self._check_admin_group():
            return False
        return True

    @api.model
    def create(self, vals):
        if vals['type'] == 'add':
            vals['date_from'] = None
            vals['date_to'] = None
        return super(HolidaysUpdated, self).create(vals)

    @api.multi
    def action_confirm(self):
        employee = self.employee_id
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError(_('Leave request must be in Draft state ("To Submit") in order to confirm it.'))
        if self.type == 'remove':
            # ********** escribir dias calendario
            self.write_number_of_days_calendar(self.date_from, self.date_to, self.employee_id.id)
            # ********** escribir dia u hora de regreso
            self.write_return_day(self.date_to, employee.id)
        # ********** enviar correo
        self.send_email_confirm_state()
        return self.write({'state': 'confirm'})

    # aprobar ausencia
    @api.multi
    def _check_security_action_approve(self):
        if not self._check_admin_group():
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

    @api.multi
    def action_approve(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        self._check_security_action_approve()

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            # if holiday.state != 'confirm' or holiday.state != 'delay':
            if holiday.state == 'draft' or holiday.state == 'refuse' or holiday.state == 'validate' or holiday.state == 'cancel':
                raise UserError('La solicitud de ausencia debe estar confirmada o aplazada para continuar con la aprobación.')

            if holiday.double_validation:
                # ********** enviar correo
                self.send_email_validate_state()
                return holiday.write({'state': 'validate1', 'first_approver_id': current_employee.id})
            else:
                holiday.action_validate()

    # validar ausencia
    @api.multi
    def _check_security_action_validate(self):
        if not self._check_admin_group():
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

    @api.multi
    def action_validate(self):
        self._check_security_action_validate()

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state == 'draft' or holiday.state == 'refuse' or holiday.state == 'validate' or holiday.state == 'cancel':
                raise UserError('La solicitud de ausencia debe estar confirmada o aplazada para continuar con la aprobación.')
            # if holiday.state not in ['confirm', 'validate1']:
                # raise UserError(_('Leave request must be confirmed in order to approve it.'))
            if holiday.state == 'validate1' and not self._check_admin_group():
                raise UserError(_('Only an HR Manager can apply the second approval on leave requests.'))

            holiday.write({'state': 'validate'})
            if holiday.double_validation:
                holiday.write({'second_approver_id': current_employee.id})
                # ********** enviar correo
                self.send_email_validate1_state()
            else:
                holiday.write({'first_approver_id': current_employee.id})
                # ********** enviar correo
                self.send_email_validate_state()
            if holiday.holiday_type == 'employee' and holiday.type == 'remove':
                holiday._validate_leave_request()
            elif holiday.holiday_type == 'category':
                leaves = self.env['hr.holidays']
                for employee in holiday.category_id.employee_ids:
                    values = holiday._prepare_create_by_category(employee)
                    leaves += self.with_context(mail_notify_force_send=False).create(values)
                # TODO is it necessary to interleave the calls?
                leaves.action_approve()
                if leaves and leaves[0].double_validation:
                    leaves.action_validate()
        return True

    # rechazar ausencia
    @api.multi
    def _check_security_action_refuse(self):
        if not self._check_admin_group():
            raise UserError(_('Only an HR Officer or Manager can refuse leave requests.'))

    @api.multi
    def action_refuse(self):
        self._check_security_action_refuse()

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate', 'validate1']:
                raise UserError(_('Leave request must be confirmed or validated in order to refuse it.'))

            if holiday.state == 'validate1':
                holiday.write({'state': 'refuse', 'first_approver_id': current_employee.id})
            else:
                holiday.write({'state': 'refuse', 'second_approver_id': current_employee.id})
            # Delete the meeting
            if holiday.meeting_id:
                holiday.meeting_id.unlink()
            # If a category that created several holidays, cancel all related
            holiday.linked_request_ids.action_refuse()
            # ********** enviar correo
            self.send_email_refuse_state()
        self._remove_resource_leave()
        return True

class HolidaysDelayState(models.Model):
    _inherit = 'hr.holidays'

    state = fields.Selection([
        ('draft', 'To Submit'), # borrador
        ('confirm', 'To Approve'), # esperando aprobación
        ('refuse', 'Refused'), # rechazada
        ('validate1', 'Second Approval'), # esperando confirmación
        ('delay', 'Postponed'), # pospuesta
        ('validate', 'Approved'), # aprobada
        ('cancel', 'Cancelled') # cancelada
    ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft')

    # posponer ausencia
    @api.multi
    def action_postponed(self):
        if not self._check_admin_group():
            raise UserError(_('Only an HR Officer or Manager can refuse leave requests.'))
        # ********** pre cpndición
        if self.filtered(lambda holiday: holiday.state != 'validate1'):
            raise UserError('La solicitud de ausencia debe estar en estado "pre aprobada" para poder aplazarla.')
        # ********** enviar correo
        self.send_email_delay_state()
        # ********** actualizar estado
        return self.write({'state': 'delay'})
