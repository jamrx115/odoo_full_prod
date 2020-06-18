# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, tools
import logging
import pytz
import re

_logger = logging.getLogger(__name__)

# actualización de vencimiento de pasaportes
class EmailsEmployeeUpdated(models.Model):
    _inherit = 'hr.employee'

    def mail_reminder(self):
        # nuevas lineas
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        now = datetime.now(tz=user_tz)

        # now = datetime.now() + timedelta(days=1)
        date_now = now.date()

        # vencimiento de identificación
        match = self.search([])
        for i in match:
            if i.id_expiry_date:
                exp_date = fields.Date.from_string(i.id_expiry_date) - timedelta(days=14)
                if date_now >= exp_date:
                    mail_content = "  Saludos  " + i.name + ",<br>Su identificación " + i.identification_id + "tiene vencimiento en " + \
                                   str(i.id_expiry_date) + ". Favor renovarlo antes de la fecha de vencimeinto"
                    main_content = {
                        'subject': _('Identificación %s con fecha de vencimiento %s') % (i.identification_id, i.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

        # vencimiento de pasaporte
        match1 = self.search([])
        for i in match1:
            if i.passport_expiry_date:
                # exp_date1 = fields.Date.from_string(i.passport_expiry_date) - timedelta(days=180)
                exp_date1 = fields.Date.from_string(i.passport_expiry_date)
                exp_is_coming = exp_date1 - timedelta(days=180)
                diferencia = (exp_date1-date_now).days

                if date_now >= exp_date1:
                    if diferencia > 0:
                        mail_content = "Por medio del presente correo se le informa,  " + i.firstname + " " + i.lastname + ",<br>Su pasaporte No. " + i.passport_id + " vence el " + \
                                       str(i.passport_expiry_date) + " (aproximadamente en " + str(diferencia) + " días). Se sugiere renovarlo antes de esta fecha."
                        subject = ('Pasaporte %s con vencimiento %s') % (i.passport_id, i.passport_expiry_date)
                    else:
                        mail_content = "Por medio del presente correo se le informa,  " + i.firstname + " " + i.lastname + ",<br>Su pasaporte No. " + i.passport_id + " ha expirado el " + \
                                       str(i.passport_expiry_date) + " (aproximadamente en " + str(diferencia) + " días). Se sugiere renovarlo antes de esta fecha."
                        subject = ('Pasaporte %s con vencimiento %s') % (i.passport_id, i.passport_expiry_date)

                    main_content = {
                        'subject': subject,
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()


        # vencimiento de visa
        for i in match1:
            if i.visa_expire:
                exp_date1 = fields.Date.from_string(i.visa_expire)
                exp_is_coming = exp_date1  - timedelta(days=180)
                diferencia = (exp_date1-date_now).days
                if date_now >= exp_is_coming:
                    if diferencia > 0:
                        mail_content = "Por medio del presente correo se le informa,  " + i.firstname + " " + i.lastname + ", su visa No. " + i.visa_no + " vence el " + \
                                   str(i.visa_expire) + " (aproximadamente en " +str(diferencia)+" dias). Se sugiere renovarla antes de esta fecha"
                        subject = _('Visa americana %s vencida el %s') % (i.visa_no, i.visa_expire)
                    else:
                        mail_content = "Por medio del presente correo se le informa,  " + i.firstname + " " + i.lastname + ", su visa No. " + i.visa_no + " ha expirado el " + \
                                   str(i.visa_expire) + " (hace " +str(-1*diferencia)+" dias). Se sugiere renovarla lo antes posible"
                        subject = ('Visa americana %s vencida el %s') % (i.visa_no, i.visa_expire)
                    main_content = {
                        'subject': subject,
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()

# actualización de vencimiento de certificaciones
class CertificationsEmployeeUpdated(models.Model):
    _inherit = 'hr.certification'

    def mail_reminder(self):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        now = datetime.now(tz=user_tz)
        #now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        for i in match:
            if i.end_date:
                exp_date1 = fields.Date.from_string(i.end_date)
                exp_is_coming = exp_date1  - timedelta(days=180)
                diferencia = (exp_date1-date_now).days
                if date_now >= exp_is_coming:
                    if diferencia > 0:
                        mail_content = "Por medio del presente correo se le informa,  " + i.employee_id.firstname + " " + i.employee_id.lastname + ", su certificado " + i.name + " No. " + i.certification + " vence el " + \
                                   str(i.end_date) + " (aproximadamente en " +str(diferencia)+" dias). Se sugiere renovarlo antes de esta fecha"
                        subject = _('Certificación %s No. %s vencida el %s') % (i.name, i.certification , i.end_date)
                    else:
                        mail_content = "Por medio del presente correo se le informa,  " + i.employee_id.firstname + " " + i.employee_id.lastname + ", su certificado " + i.name + " No. " + i.certification + " ha expirado el " + \
                                   str(i.end_date) + " (hace " +str(-1*diferencia)+" dias). Se sugiere renovarlo lo antes posible"
                        subject = ('Certificación %s No. %s vencida el %s') % (i.name, i.certification, i.end_date)
                    main_content = {
                        'subject': subject,
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.employee_id.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()