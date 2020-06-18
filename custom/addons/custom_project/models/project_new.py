# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, time
from odoo import fields, models, api, tools
from odoo.exceptions import UserError
import logging
import pytz
import re

_logger = logging.getLogger(__name__)
# _logger.debug('abc')
# _logger.debug('var ===> %s', var)

# Personalización de etapas de tareas de proyectos
class ProjectTaskTypeCustom(models.Model):
    _inherit = 'project.task.type'

    progress_min = fields.Float('Progreso Mínimo (%)')
    progress_max = fields.Float('Progreso Máximo (%)')

# Personalización de tareas de proyectos
class ProjectTaskCustom(models.Model):
    _inherit = 'project.task'

    label_task = fields.Char(related='project_id.label_tasks', store=True)
    current_progress = fields.Float(string="Progreso general de la tarea (%)", help="De 0.0 a 100.0, debe estar entre los límites mínimo y máximo del estado actual de la tarea.")
    act_id = fields.Many2one('custom.project.act', string='Acta Nro.')

    @api.multi
    def write(self, vals):
        for obj in self:
            old_stage_obj = obj.stage_id
            old_progress = obj.current_progress
            lim_min = old_stage_obj.progress_min
            lim_max = old_stage_obj.progress_max

            # *** si cambia de estado (anterior o posterior al actual), escribe nuevo progreso
            new_stage = vals.get('stage_id')
            if new_stage:
                new_stage_obj = self.env['project.task.type'].browse(new_stage)
                lim_min = new_stage_obj.progress_min
                lim_max = new_stage_obj.progress_max
                vals['current_progress'] = lim_min

            # *** si cambia de progreso por fuera de los límites, lanzar ERROR
            possible_new_progress = vals.get('current_progress')
            if possible_new_progress:
                if not new_stage:
                    if ((possible_new_progress < lim_min) or (possible_new_progress > lim_max)):
                        raise UserError(('"Progreso general de la tarea" no válido, debe estar entre %s y %s. Puede regresar a %s.') % (lim_min, lim_max, old_progress))

        return super(ProjectTaskCustom, self).write(vals)

# Actas por proyecto
class CustomProjectAct (models.Model):
    _name = "custom.project.act"
    _description = "Actas de proyectos"
    _inherit = ['mail.thread']

    name = fields.Char(string="Nombre")
    date = fields.Date(string="Fecha de reunión", default=datetime.today().date())
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('created', 'Acta Creada'),
        ('closed', 'Cerrada'),
        ], default='draft', string='Estado', track_visibility='onchange')
    project_id = fields.Many2one('project.project', string='Proyecto', default=lambda self: self.env.context.get('default_project_id'))
    # employee_ids = fields.Many2many('hr.employee', string='Asistentes')
    partner_ids = fields.Many2many('res.partner', string='Asistentes', domain="['|', ('parent_id', '!=', None), ('employee', '=', True)]")
    details = fields.Text(string="Agenda y Temas tratados")
    conclusion = fields.Text(string="Conclusiones y compromisos")
    task_ids = fields.One2many('project.task', 'act_id', 'Tareas', help="Tareas asignadas en el acta de reunión.")

    @api.model
    def create(self, vals):
        count = self.env['custom.project.act'].search_count([('project_id', '=', vals.get('project_id'))])
        project = self.env['project.project'].browse(vals.get('project_id'))
        name = "AT-Acta(" + str(count+1) + ")" + project.name
        vals['name'] = name
        return super(CustomProjectAct, self).create(vals)

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state in ('closed'):
                raise UserError(('No puede borrar el acta dado que ya se encuentra cerrada.'))
            else:
                return models.Model.unlink(obj)

    # status draft to created
    @api.multi
    def action_start(self):
        for obj in self:
            if obj.state != 'draft':
                raise UserError('El acta debe estar en borrador para iniciar proceso.')
            obj.write({ 'state': 'created', })

    # status created to closed
    @api.multi
    def action_end(self):
        for obj in self:
            if obj.state != 'created':
                raise UserError('El acta debe estar creada para cerrar el proceso.')
            obj.write({ 'state': 'closed', })
