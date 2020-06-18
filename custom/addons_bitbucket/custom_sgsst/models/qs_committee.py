# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.resource import to_naive_utc, to_naive_user_tz, to_tz

from datetime import datetime

import logging
import re

_logger = logging.getLogger(__name__)
# _logger.debug('---------------')
# _logger.debug('user_id %s', user_id)

# -------------------- auxiliares ---------------------
# notas
class CustomAssignmentNote(models.Model):
    _name = "custom.assignment.note"
    _description = "Notas SG-SST"
    _inherit = ['mail.thread']

    qs_id = fields.Many2one('custom.qscommittee', string="Queja / Sugerencia ID")
    # se usarán en las vistas los campos ID y create_date
    name = fields.Char(string="Descripción corta")
    observations = fields.Text('Observaciones o documentos aportados')

    assign_id = fields.Many2one('custom.committee.applicant', string='Responsable', help="Responsable de la queja o sugerencia")

    # *************** override ****************
    @api.model
    def create(self, vals):
        qs_obj = self.env['custom.qscommittee'].browse(vals['qs_id'])
        vals['assign_id'] = qs_obj.assign_id.id
        return super(CustomAssignmentNote, self).create(vals)

# --------------------- principal ---------------------

# quejas y sugerencias a sst
class CustomQsCommittee (models.Model):
    _name = "custom.qscommittee"
    _description = "Quejas y Sugerencias SST"
    _inherit = ['mail.thread']

    # funciones auxiliares
    @api.model
    def _getfilter_assigned(self):
        # campos del modelo custom.committee.applicant
        # resource = self.env['resource.resource'].search([('user_id','=',self.env.user.id)])
        # employee = self.env['hr.employee'].search([('resource_id','=',resource.id)])
        domain_filter = ['&', ('type_comm', '=', 'CC'), ('state', '=', 'activo')]
        return domain_filter

    # se usarán en las vistas los campos ID y create_date
    # state = draft
    name = fields.Char(string="Nombre")
    employee_id = fields.Many2one('hr.employee', string='Empleado', domain=[('active', '=', True)], track_visibility="onchange")
    id_str = fields.Char(string="Documento identidad")
    dp_str = fields.Char(string="Departamento")
    job_str = fields.Char(string="Cargo")
    case_type = fields.Selection([
        ('queja','Queja'),
        ('sugerencia','Sugerencia')
        ], string="Tipo de caso", required=True, track_visibility="onchange")
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('start', 'Asignación'),
        ('tracing', 'Seguimiento'),
        ('solved', 'Resuelto'),
        ('closed', 'Cerrado')
        ], default='draft', string='Estado', track_visibility='onchange')
    description_qs = fields.Text('Descripción')
    test_and_fixes = fields.Text('Observaciones')
    seq_name = fields.Integer('Sequencia por tipo', default=1)
    # state = start
    assign_id = fields.Many2one('custom.committee.applicant', string='Responsable actual', domain=_getfilter_assigned, track_visibility="onchange")
    date = fields.Date(string="Fecha compromiso", track_visibility="onchange")    
    notes = fields.One2many('custom.assignment.note', 'qs_id', string="Notas")
    # state = tracing
    abstract_tracing = fields.Text('Resumen')
    answer_tracing = fields.Text('Respuesta')
    # state = solved
    abstract_solved = fields.Text('Resumen')
    answer_solved = fields.Text('Respuesta')
    comment_solved = fields.Text('Comentarios del colaborador')
    # state = closed
    date_close = fields.Date(string="Fecha de cierre")

    # **************** onchange ****************
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.id_str = self.employee_id.identification_id
        self.dp_str = self.employee_id.department_id.name
        self.job_str = self.employee_id.job_id.name
        self.description_qs = ''
        self.test_and_fixes = ''

    @api.onchange('case_type')
    def _onchange_case_type(self):
        self.description_qs = ''
        self.test_and_fixes = ''

    # *************** override ****************
    def send_email_newcase(self):
        template = self.env.ref('custom_sgsst.create_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    @api.model
    def create(self, vals):
        employee = self.env['hr.employee'].browse(vals['employee_id'])
        vals['id_str'] = employee.identification_id
        vals['dp_str'] = employee.department_id.name
        vals['job_str'] = employee.job_id.name

        last_seq_name = self.env['custom.qscommittee'].search([('case_type', '=', vals['case_type'])], order = 'create_date desc', limit=1).seq_name
        if last_seq_name:
            vals['seq_name'] = last_seq_name + 1
            vals['name'] = vals['case_type'] + " " + str(last_seq_name + 1)
        else:
            vals['seq_name'] = 1
            vals['name'] = vals['case_type'] + " 1"

        res = super(CustomQsCommittee, self).create(vals)
        res.send_email_newcase()

        return res

    @api.multi
    def write(self, values):
        if values.get('assign_id'):
            now_utc  = datetime.now() # utc cero
            values['date'] = to_naive_user_tz(now_utc, self.env.user)
        res = super(CustomQsCommittee, self).write(values) # bool
        return res

    @api.multi
    def unlink(self):
        for qs in self:
            if qs.state in ('closed'):
                raise UserError(('No puede borrar el caso %s ya que está cerrado') % (qs.name),)
            elif qs.state in ('start'):
                raise UserError(('No puede borrar el caso %s ya que ha iniciado ejecución.') % (qs.name),)
            elif qs.state in ('tracing'):
                raise UserError(('No puede borrar el caso %s ya que ha iniciado seguimiento.') % (qs.name),)
            elif qs.state in ('solved'):
                raise UserError(('No puede borrar el caso %s ya que ha iniciado solución.') % (qs.name),)
            else:
                return models.Model.unlink(qs)

    # ************** state changes **************
    # status nuevo to inicio
    @api.multi
    def action_start(self):
        for obj in self:
            if obj.state != 'draft':
                raise UserError('La presentación de la queja debe estar en estado Nuevo para iniciar ejecución.')
            else:
                obj.write({ 'state': 'start', })
                # ********** enviar correo
                template = self.env.ref('custom_sgsst.start_template')
                self.env['mail.template'].browse(template.id).send_mail(self.id)

    # status inicio to seguimiento
    @api.multi
    def action_tracing(self):
        for obj in self:
            if obj.state != 'start':
                raise UserError('La presentación de la queja debe estar asignada para iniciar seguimiento.')
            else:
                obj.write({ 'state': 'tracing', })

    # status seguimiento to resuelto
    @api.multi
    def action_solve(self):
        for obj in self:
            if obj.state != 'tracing':
                raise UserError('La presentación de la queja debe estar en seguimiento para iniciar solución.')
            else:
                obj.write({ 'state': 'solved', })

    # status resuelto to cerrado
    @api.multi
    def action_close(self):
        for obj in self:
            if obj.state != 'solved':
                raise UserError('La presentación de la queja debe estar en solución para iniciar cierre.')
            else:
                now_utc  = datetime.now()
                obj.write({ 'date_close': to_naive_user_tz(now_utc, self.env.user), })
                obj.write({ 'state': 'closed', })
                # ********** enviar correo
                template = self.env.ref('custom_sgsst.closed_template')
                self.env['mail.template'].browse(template.id).send_mail(self.id)
