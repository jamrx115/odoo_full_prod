# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime

import logging
import re

_logger = logging.getLogger(__name__)

# --------------------- estado análisis ---------------------

# Tipo de entregable
class CustomEntregablePQRS(models.Model):
    _name = "custom.pqrs.deliver"
    _description = "Tipos de entregable"
    _inherit = ['mail.thread']

    name = fields.Char(string="Tipo de entregable", track_visibility='onchange')

# Proceso afectado
class CustomAffectedProcessPQRS(models.Model):
    _name = "custom.pqrs.affected.process"
    _description = "Proceso"
    _inherit = ['mail.thread']

    name = fields.Char(string="Proceso", track_visibility='onchange')

# Causas identificadas
class CustomCausesPQRS(models.Model):
    _name = "custom.pqrs.causes"
    _description = "Causa identificada"
    _inherit = ['mail.thread']

    name = fields.Char(string="Proceso", track_visibility='onchange')

# Metodologías
class CustomMethodPQRS(models.Model):
    _name = "custom.pqrs.method"
    _description = "Metodología"
    _inherit = ['mail.thread']

    name = fields.Char(string="Metodología", track_visibility='onchange')

# Oportunidades de mejora
class CustomOpportunityPQRS(models.Model):
    _name = "custom.pqrs.opportunity"
    _description = "Oportunidades de mejora"
    _inherit = ['mail.thread']

    name = fields.Char(string="Oportunidad de mejora", track_visibility='onchange')

# --------------------- estado respuesta ---------------------

# Correo de notificación al cliente

# Evidencia adjunta de acción de mejora

# --------------------- estado validación de respuesta ---------------------

# Evidencia de respuesta del cliente - cuadro de texto o adjunto

# --------------------- estado cierre ---------------------

# Encuesta de verificación de respuesta recibida

# --------------------- clase principal ---------------------

# peticiones, quejas, reclamos y sugerencias
class CustomPqrs (models.Model):
    _name = 'custom.pqrs'
    _description = "Quejas, reclamos y sugerencias"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'custom.claim']

    # funciones auxiliares
    @api.model
    def _getfilter_employee(self):
        return ['&', ('active', '=', True), ('employee', '=', True)]

    @api.model
    def _getfilter_partner(self):
        return ['&', '&', ('active', '=', True), ('customer', '=', True), ('parent_id', '=', False)]

    @api.model
    def _getfilter_contact(self):
        return ['&', '&', ('active', '=', True), ('customer', '=', True), ('parent_id', '!=', False)]

    # atributos
    employee_id = fields.Many2one('res.users', string='Asignado a', domain=_getfilter_employee, track_visibility="onchange")
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('analysis', 'Análisis'),
        ('answered', 'Respuesta'),
        ('confirmed', 'Validación de Solución'),
        ('close', 'Cierre'),
        ('closed', 'Cerrado')
        ], default='draft', string='Estado', track_visibility='onchange')
    type_sel = fields.Selection([
        #('peticion','Petición'),
        ('queja','Queja'),
        ('reclamo','Reclamo'),
        ('sugerencia','Sugerencia')
        ], 
        string="Tipo de registro", track_visibility="onchange")
    customer_id = fields.Many2one('res.partner', string='Cliente', domain=_getfilter_partner, track_visibility="onchange")
    contact_id = fields.Many2one('res.partner', string='Contacto', domain=_getfilter_contact, track_visibility="onchange")
    project_id = fields.Many2one('project.project', string='Proyecto', track_visibility="onchange")

    # analysis stage
    deliverable_ids = fields.Many2many('custom.pqrs.deliver', string='Tipos de entregable')
    affprocess_id   = fields.Many2one('custom.pqrs.affected.process', string='Proceso afectado', track_visibility="onchange")
    cause_id        = fields.Many2one('custom.pqrs.causes', string='Causa identificada', track_visibility="onchange")
    cause_note      = fields.Text('Nota de causa raíz')
    cause_method_id = fields.Many2one('custom.pqrs.method', string='Metodología seleccionada', track_visibility="onchange")
    answer          = fields.Text('Respuesta a proponer')
    opportunity_ids = fields.Many2many('custom.pqrs.opportunity', string='Oportunidades de mejora')
    # answered stage
    subject = fields.Char(string="Asunto")
    mail_body = fields.Html('Cuerpo de Correo')
    # validation stage
    name_answer_validation = fields.Selection([
        ('texto', 'Descripción de respuesta'),
        ('adjunto', 'Adjunto')
        ], default='texto', string='Tipo de respuesta', required=True, track_visibility="onchange")
    description_answer_validation = fields.Text('Evidencia de respuesta', track_visibility="onchange")
    # close stage
    answer_time = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
        ], default='5', string='¿Cómo fue el tiempo de respuesta para su petición o reclamo?')
    answer_close = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
        ], default='5', string='¿Se solucionó totalmente su queja o reclamo?')
    answer_treatment = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
        ], default='5', string='¿Cómo fué el trato recibido en el proceso?')

    # onchange
    @api.multi
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        self.project_id = False
        if self.customer_id:
            return {'domain': {'project_id': [('partner_id', '=', self.customer_id.id)], 
                               'contact_id': [('parent_id', '=', self.customer_id.id)]}}
        else:
            return {'domain': {'project_id': [], 'contact_id': []}}

    ##
    @api.multi
    @api.onchange('x_residence_country_id')
    def _onchange_country_id(self):
        self.x_residence_state_id = False
        self.x_residence_city_id = False
        if self.x_residence_country_id:
            return {'domain': {'x_residence_state_id': [('country_id', '=', self.x_residence_country_id.id)]}}
        else:
            return {'domain': {'x_residence_state_id': []}}
    ##

    @api.multi
    @api.onchange('name_answer_validation')
    def _onchange_name_answer_validation(self):
        if self.name_answer_validation == 'adjunto':
            self.description_answer_validation = False

    # override
    @api.multi
    def unlink(self):
        for pqrs in self:
            if pqrs.state in ('closed'):
                raise UserError(('No puede borrar un PQRS que esté cerrado.'))
            else:
                return models.Model.unlink(pqrs)

    # status draft to analysis
    @api.multi
    def action_new(self):
        for obj in self:
            if obj.state != 'draft':
                raise UserError('El PQRS debe estar en borrador para iniciar flujo PQRS.')
            obj.write({ 'state': 'analysis', })

    # status analysis to answered
    @api.multi
    def action_analysis(self):
        for obj in self:
            if obj.state != 'analysis':
                raise UserError('El PQRS debe estar en análisis para llevarlo a llevarlo a Respuesta.')
            obj.write({ 'state': 'answered', })

    # status answered to confirmed
    @api.multi
    def action_answered(self):
        for obj in self:
            if obj.state != 'answered':
                raise UserError('El PQRS debe estar en respuesta para llevarlo a Validación de Solución.')

            obj.write({ 'state': 'confirmed', })

    # send_email
    def send_email_customer(self):
        main_content = {
                        'email_from': self.employee_id.email,
                        'email_to': self.customer_id.email,
                        'subject': self.subject,
                        'body_html': self.mail_body,
                    }
        self.env['mail.mail'].sudo().create(main_content).send()

    # status confirmed to close
    @api.multi
    def action_confirmed(self):
        for obj in self:
            if obj.state != 'confirmed':
                raise UserError('El PQRS debe estar en validación de solución para llevarlo a Cierre.')

            obj.write({ 'state': 'close', })

    # status close to closed
    @api.multi
    def action_closed(self):
        for obj in self:
            if obj.state != 'close':
                raise UserError('El PQRS debe estar en etapa de cierre para finalizar flujo.')
            obj.write({ 'state': 'closed', })

