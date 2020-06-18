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
class CustomEmployee(models.Model):
    _inherit = 'hr.employee'

    # ---------- nuevos campos identification
    x_identification_type = fields.Selection([ 
        ('12', 'Tarjeta de identidad'), 
        ('13', 'Cédula de ciudadanía'),
        ('21', 'Tarjeta de extranjería'),
        ('22', 'Cédula de extranjería'),
        ('31', 'NIT'), 
        # ('41', 'Pasaporte'), 
        ('42', 'Documento de identificación extranjero'), 
        ('43', 'Sin identificación del exterior o para uso definido por la DIAN') ], 
        string='Tipo identificación', groups="base.group_user")
    x_nit = fields.Char('NIT', compute="_compute_checkdigit", store=True, readonly=True, groups="base.group_user")
    x_check_digit = fields.Integer(string='Dígito de verificación', compute="_compute_checkdigit", store=True, readonly=True, groups="base.group_user")
    x_blood_name = fields.Selection([ ('O', 'O'), ('A', 'A'), ('B', 'B'), ('AB', 'AB') ], string='Grupo sanguíneo', groups="base.group_user")
    x_blood_type = fields.Selection([ ('-', '-'), ('+', '+') ], string='RH', groups="base.group_user")
    x_address = fields.Char('Dirección personal', groups="base.group_user")
    x_personal_email = fields.Char('Correo electrónico personal')
    
    # ---------- nuevos campos residencia
    x_residence_country_id = fields.Many2one("res.country", string='País de residencia', groups="base.group_user")
    x_residence_state_id = fields.Many2one("res.country.state", string='Estado/Departamento', ondelete='restrict', groups="base.group_user")
    x_residence_city_id = fields.Many2one("res.city", string='Ciudad de Residencia', ondelete='restrict', groups="base.group_user")
    x_personal_mobile = fields.Char(string='Móvil personal', groups="base.group_user")
        
    # ---------- nuevos campos nacimiento
    x_birth_country_id = fields.Many2one("res.country", string="País de Nacimiento", ondelete='restrict', groups="base.group_user")
    x_birth_state_id = fields.Many2one("res.country.state", string='Estado/Departamento', ondelete='restrict', groups="base.group_user")
    x_birth_city_id = fields.Many2one("res.city", string='Ciudad de Nacimiento', ondelete='restrict', groups="base.group_user")
    
    # ---------- nuevos campos company
    x_work_country_id = fields.Many2one("res.country", string='Ubicación de trabajo', readonly=True, groups="base.group_user")

    # ---------- nuevas funciones
    # Dígito de verificación
    @api.depends('identification_id')
    def _compute_checkdigit(self):
        for record in self:
            colombia = record.env['res.country'].search([['name', '=', 'Colombia']])
            if record.identification_id:
                if record.country_id == colombia:
                    if record.identification_id.isdigit():
                        cantidad_ceros = 15-len(record.identification_id)
                        string_base = str(0)*cantidad_ceros+str(record.identification_id)
                        auxiliar_base = int(string_base[14:15])*3 + int(string_base[13:14])*7 + int(string_base[12:13])*13 + \
                                        int(string_base[11:12])*17 + int(string_base[10:11])*19 + int(string_base[9:10])*23 + \
                                        int(string_base[8:9])*29 + int(string_base[7:8])*37 + int(string_base[6:7])*41 + \
                                        int(string_base[5:6])*43 + int(string_base[4:5])*47 + int(string_base[3:4])*53 + \
                                        int(string_base[2:3])*59 + int(string_base[1:2])*67 + int(string_base[0:1])*71
                        auxiliar = auxiliar_base % 11
                        if auxiliar == 0:
                            record.x_check_digit = 0
                        elif auxiliar == 1:
                            record.x_check_digit = 1
                        else:
                            record.x_check_digit = 11-auxiliar
                        # guardando el campo NIT
                        record.x_nit = str(record.identification_id)+'-'+str(record.x_check_digit)
                    else:
                        raise UserError('En Colombia los NIT deben ser numéricos')
                else:
                    record.x_check_digit  = 0
                    record.x_nit = record.identification_id

    # Funciones datos residencia
    @api.multi
    @api.onchange('x_residence_country_id')
    def _onchange_country_id(self):
        self.x_residence_state_id = False
        self.x_residence_city_id = False
        if self.x_residence_country_id:
            return {'domain': {'x_residence_state_id': [('country_id', '=', self.x_residence_country_id.id)]}}
        else:
            return {'domain': {'x_residence_state_id': []}}

    @api.multi
    @api.onchange('x_residence_state_id')
    def _onchange_state_id(self):
        if self.x_residence_state_id:
            return {'domain': {'x_residence_city_id': [('state_id', '=', self.x_residence_state_id.id)]}}
        else:
            return {'domain': {'x_residence_city_id': []}}

    # Funciones datos nacimiento
    @api.multi
    @api.onchange('x_birth_country_id')
    def _onchange_birth_country_id(self):
        self.x_birth_state_id = False
        self.x_birth_city_id = False
        if self.x_birth_country_id:
            return {'domain': {'x_birth_state_id': [('country_id', '=', self.x_birth_country_id.id)]}}
        else:
            return {'domain': {'x_birth_state_id': []}}

    @api.multi
    @api.onchange('x_birth_state_id')
    def _onchange_birth_state_id(self):
        if self.x_birth_state_id:
            return {'domain': {'x_birth_city_id': [('state_id', '=', self.x_birth_state_id.id)]}}
        else:
            return {'domain': {'x_birth_city_id': []}}

    # Plantillas para campos (expresiones regulares)
    @api.multi
    @api.onchange('x_foreigner_identification')
    def _check_value_idn(self):
        if self.x_foreigner_identification:
            pattern = "^\w[a-zA-Z0-9_\-]{7,19}$"
            if re.match(pattern, self.x_foreigner_identification) == None:
                self.x_foreigner_identification = ""
                return {
                    'warning': {'title': _('Error'),
                                'message': 'Formato de número de identificación no valido, debe incluir términos alfanúmeros y guion (si aplica), longitud máxima de caracteres 20', }
                }

# Clase que gestiona el nombre del empleado
class NamesEmployee(models.Model):
    _inherit = 'hr.employee'

    # ---------- nuevos campos nombres
    first_name = fields.Char(string="Primer Nombre", required=True)
    middle_name = fields.Char(string="Siguientes Nombres")
    last_name = fields.Char(string="Primer Apellido", required=True)
    second_last_name = fields.Char(string="Segundo Apellido")

    @api.onchange('first_name', 'middle_name', 'last_name', 'second_last_name')
    def _onchange_employee_name(self):
        names = [name for name in [self.first_name, self.middle_name, self.last_name, self.second_last_name] if name]
        self.name = ' '.join(names)

# Clase que actualiza datos de empleado a contacto
class ContactEmployee(models.Model):
    _inherit = 'hr.employee'

    current_leave_state = fields.Selection(compute='_compute_leave_status', string="Current Leave Status",
        selection=[
            ('draft', 'To Submit'), # borrador
            ('confirm', 'To Approve'), # esperando aprobación
            ('refuse', 'Refused'), # rechazada
            ('validate1', 'Second Approval'), # esperando confirmación
            ('delay', 'Postponed'), # pospuesta
            ('validate', 'Approved'), # aprobada
            ('cancel', 'Cancelled') # cancelada
        ])

    def update_user_data(self):
        limite = datetime.now() - timedelta (days=7)
        employees = self.env['hr.employee'].search(['&',('active', '=', True),('write_date', '>', str(limite))])
        for employee in employees:
            user = employee.resource_id.user_id
            if user:
                partner = user.partner_id
                partner.write({'vat': employee.identification_id})
                user.write({'name': employee.name})
                user.write({'first_name': employee.first_name, 'middle_name':employee.middle_name})
                user.write({'last_name': employee.last_name, 'second_last_name':employee.second_last_name})
                if partner.employee == False:
                    partner.write({'customer': False, 'supplier':False, 'employee': True})
                if employee.x_personal_mobile:
                    user.write({'mobile': employee.x_personal_mobile})
                if employee.job_id:
                    user.write({'function': employee.job_id.name})
                if employee.image:
                    user.write({'image': employee.image})
                    user.write({'image_medium': employee.image_medium})
                    user.write({'image_small': employee.image_small})
                if employee.work_email:
                    user.write({'email': employee.work_email})
                if employee.x_address:
                    user.write({'street': employee.x_address})
                if employee.x_residence_state_id:
                    user.write({'state_id': employee.x_residence_state_id.id})
                if employee.x_residence_country_id:
                    user.write({'country_id': employee.x_residence_country_id.id})

# clase creada por alltic que modifica empleado para nomina
class PayrollEmployee(models.Model):
    _inherit = 'hr.employee'

    #
    payslip_count = fields.Integer(compute='_compute_payslip_count', string='Payslips')

    # ---------- nuevas funciones
    def is_leap_year(self):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        current_year = datetime.now(tz=user_tz).year

        if current_year % 4 == 0:
            if current_year % 100 == 0:
                if current_year % 400 == 0:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False

    def get_age(self):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        fecha_nacimiento = fields.Datetime.from_string(self.birthday).date()
        hoy = datetime.now(tz=user_tz).date()
        return (hoy - fecha_nacimiento).days / 365

    def get_filtered_lineid(self, code):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        last_year = (datetime.now(tz=user_tz).date().year) - 1
        aux = 0
        for m in range(12):
            mes = m + 1
            date_from = datetime(day=1, month=mes, year=last_year).date()
            date_to = datetime(day=calendar.monthrange(last_year, mes)[1], month=mes, year=last_year).date()
            pagos = self.env['hr.payslip'].search(
                ['&', '&', '&', ('date_from', '>=', date_from), ('date_to', '<=', date_to),
                 ('employee_id', '=', self.id), ('state', '=', 'done')],
                order="date_from")
            for nomina in pagos:
                line_ids = nomina.line_ids
                for line in line_ids:
                    if line.code == code:
                        aux += line.total
        return aux