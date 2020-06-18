# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.exceptions import UserError, ValidationError
from openerp.exceptions import except_orm, Warning, RedirectWarning

from datetime import datetime

import logging
import re

_logger = logging.getLogger(__name__)

# evaluación de desempeño
class CustomPerformance (models.Model):
    _name = "custom.performance"
    _description = "Evaluaci&oacute;n de desempe&ntilde;o"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Many2one('res.users', string='Nombre del empleado', track_visibility="onchange")
    evaluator_id = fields.Many2one('res.users', string="Evaluador", track_visibility="onchange")
    date = fields.Date(string = "Fecha", help="Ingrese la fecha de creación de la evaluación")
    
    performance_goal_id = fields.One2many('custom.performance.line','custom_performance_id',string="Objetivos de rendimiento")
    performance_goal_id_2 = fields.One2many('custom.performance.line','custom_performance_id',string="Objetivos de rendimiento 2")

    evolution_personal_goal_id = fields.One2many('custom.personal.goals','custom_performance_id', string="Objetivos de desarrollo personal")
    
    general_rating = fields.Selection([('excepcional', 'Excepcional'),('sobresaliente', 'Sobresaliente'),('bueno', 'Bueno'),('mejor', 'Necesita mejorar'),],string="Calificación general", track_visibility="onchange")
    comments_extra = fields.Text(string="Comentarios adicionales")
    department_id = fields.Many2one('hr.department', string="Departamento")
    type_evaluation = fields.Selection([
        ('evaluacion', 'Evaluación de desempeño'),
        ('prueba', 'Periodo de adaptación')
    ],string='Tipo')
    state = fields.Selection([('borrador','Borrador'),('primer','Autoevaluación'),('segundo','Evaluación líder'),('finalizada','Finalizada')], string="Estado de periodo de adaptación", track_visibility="onchange",default="borrador")
    state2 = fields.Selection([('borrador','Borrador'),('calif1','Calificación 1'),('calif2','Calificación 2'),('calif3','Calificación 3'),('finalizada','Finalizada')], string="Estado de evaluación de desempeño", track_visibility="onchange",default="borrador")

    joining_date = fields.Date(string = "Fecha Ingreso", editable=False, copy=True, help="Fecha tomada de los datos del empleado")
    immediate_boss = fields.Char(string="Jefe inmediato", editable=False, copy=True)

    #Acciones del primer modelo de evaluación
    @api.one
    def action_primer_semestre(self):
        self.write({
            'state': 'primer',
        })
    @api.one
    def action_segundo_semestre(self):
        self.write({
            'state': 'segundo',
        })
    #Acciones del segundo modelo de evaluación
    @api.one
    def action_primera_calificacion(self):
        self.write({
            'state2': 'calif1',
        })
    @api.one
    def action_segunda_calificacion(self):
        self.write({
            'state2': 'calif2',
        })
    @api.one
    def action_tercera_calificacion(self):
        self.write({
            'state2': 'calif3',
        })
    
    #Acciones generales para los 2 modelos    
    @api.one
    def action_end_performance(self, values):
        if self.general_rating == False:
           raise UserError('Antes de terminar la evaluación debe ingresar la calificación general del colaborador')
        if self.type_evaluation == 'evaluacion':
            self.write({
                'state2': 'finalizada',
            })
        elif self.type_evaluation == 'prueba':
            self.write({
                'state': 'finalizada',
            })


    @api.one
    def action_back_performance(self):
        if self.type_evaluation == 'evaluacion':
            self.write({
                'state2': 'calif1',
            })
        elif self.type_evaluation == 'prueba':
            self.write({
                'state': 'primer',
            })

    @api.model
    def create(self, values):
        values['state'] = None
        values['state2'] = None
        resource = self.env['resource.resource'].search([('user_id', '=', values['name'])])
        employee = self.env['hr.employee'].search([('resource_id', '=', resource.id)])
        values['joining_date']   = employee.joining_date
        values['immediate_boss'] = employee.parent_id.name
        if values.get('type_evaluation') == 'evaluacion':
            values['state2'] = 'calif1'
        elif values.get('type_evaluation') == 'prueba':
            values['state'] = 'primer'
        res = super(CustomPerformance,self.with_context(mail_create_nosubscribe=True)).create(values)
        return res

    @api.multi
    def write(self, values):
        res = super(CustomPerformance, self).write(values) # bool
        if values.get('name'):
            resource = self.env['resource.resource'].search([('user_id', '=', values.get('name'))])
            employee = self.env['hr.employee'].search([('resource_id', '=', resource.id)])

            values['joining_date']   = employee.joining_date
            values['immediate_boss'] = employee.parent_id.name
            res = super(CustomPerformance, self).write(values) # bool
        return res
     
    #Carga los objetivos del área del colaborador y cuando se vuelve a llamar formatea y vuelve a iniciar.
    @api.multi
    def get_goal(self):
        goal_list = []
        # elimina las filas asociadas
        self.env['custom.performance.line'].search([('custom_performance_id.id', '=', self.id)]).unlink()
        # busca el tipo de evaluación (lista de ids objetivos generales)
        classification_filterp = self.env['custom.main.goals'].search([('classification', '=', 'all')]).ids
        classification_filter  = classification_filterp + self.env['custom.main.goals'].search([('classification', '=', self.type_evaluation)]).ids
        # busca los objetivos específicos para el empleado
        goals_of_this_employee = self.env['custom.goals'].search(['&', ('departments_ids', '=', self.department_id.id), ('main_goal_related_id', 'in', classification_filter)])
        # crea las nuevas filas asociadas
        for goal in goals_of_this_employee:
            goal_created  = self.env['custom.performance.line'].create({
                            'goal_id': goal.id})
            goal_list.append(goal_created.id)
        self.performance_goal_id = goal_list
        return goal_list



    
    # Modificación de vista según el tipo de evaluación
    #@api.onchange('type_evaluation')
    #def change_view(self):
    #    if self.type_evaluation == 'prueba':
    #        type_evaluation_stored == False
    #    else type_evaluation_stored == True





        
# Objetivos de rendimiento    
class CustomPerformanceLine (models.Model):
    _name="custom.performance.line"
    _description = "Objetivos de rendimiento"

    custom_performance_id = fields.Many2one('custom.performance',string="conexión")
    name = fields.Char(string="Nombre")
    sequence = fields.Integer(string="secuencia")
    main_goal_id = fields.Many2one('custom.main.goals',related="goal_id.main_goal_related_id", string="objetivo general")   
    goal_id = fields.Many2one('custom.goals',string="Objetivo específico")
    description_from_goals = fields.Text(string='Descripción', related="goal_id.description")
    
    Autoevaluation = fields.Char(string="Autoevaluación")
    leader_evaluation = fields.Char(string="Evaluación líder")
    final_evaluation = fields.Char(string="Evaluación final")
    personal_goal = fields.Char(string="Meta personal")
    comments_employee = fields.Text(string="Comentarios empleado")
    comments_evaluator = fields.Text(string="Comentarios evaluador")

    qualification_1 = fields.Char(string="Calificación 1")
    qualification_2 = fields.Char(string="Calificación 2")
    qualification_3 = fields.Char(string="Calificación 3")
    final_qualification = fields.Char(string="Calificación final")
    comments_employee = fields.Text(string="Comentarios empleado")
    comments_evaluator = fields.Text(string="Comentarios evaluador")


    #cambia el objetivo general dependiendo del objetivo especifico
    @api.onchange('goal_id')
    def _onchange_goals(self):
        self.main_goal_id = self.goal_id.main_goal_related_id

    #cambia la descripción dependiendo del objetivo especifico
    @api.onchange('goal_id')
    def _onchange_goals(self):
        self.description_from_goals = self.goal_id.description

# objetivos generales
class CustomMainGoals (models.Model):
    _name="custom.main.goals"
    _description = "Objetivo estrategia general"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre')
    description = fields.Text(string='Descripción')
    short_descr = fields.Text(string='Descripción', compute='_compute_short_descr')
    goal = fields.Char(string='Meta')
    comments = fields.Text(string='Comentarios')
    classification = fields.Selection([
        ('evaluacion', 'Evaluación de desempeño'),
        ('prueba', 'Periodo de adaptación'),
        ('all', 'Todas')
    ], string='Tipo')
    active = fields.Boolean(string="Activo", default="True")

    @api.depends('description')
    @api.onchange('description')
    def _compute_short_descr(self):
        for rec in self:
            if rec.description:
                rec.short_descr = (rec.description[:48] + '..') if len(rec.description) > 50 else rec.description
    
    @api.model
    def create(self, values):
        res = super(CustomMainGoals,self.with_context(mail_create_nosubscribe=True)).create(values)
        return res

    @api.multi
    def unlink(self):
        range_obj = self.env['custom.goals']
        rule_ranges = range_obj.search([('main_goal_related_id', 'in', self.ids)])
        if rule_ranges:
            raise Warning(_("¡Está tratando de eliminar un objetivo de estrategia general que aun está siendo usado!"))
        return super(CustomMainGoals, self).unlink()

# objetivos específicos
class CustomGoals (models.Model):
    _name="custom.goals"
    _description = "Objetivo especifico"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre')
    main_goal_related_id = fields.Many2one('custom.main.goals', string="Objetivo de estrategia general")
    description = fields.Text(string='Descripción')
    short_descr = fields.Text(string='Descripción', compute='_compute_short_descr')
    departments_ids = fields.Many2many('hr.department',string="Departamento")
    goal = fields.Char(string='Meta')
    goal_min = fields.Char(string='Mínimo')
    goal_max = fields.Char(string='Máximo')
    active = fields.Boolean(string="Activo", default="True")

    @api.depends('description')
    @api.onchange('description')
    def _compute_short_descr(self):
        for rec in self:
            if rec.description:
                rec.short_descr = (rec.description[:48] + '..') if len(rec.description) > 50 else rec.description

    @api.model
    def create(self, values):
        res=super(CustomGoals,self.with_context(mail_create_nosubscribe=True)).create(values)
        return res

    @api.multi
    def unlink(self):
        range_obj = self.env['custom.performance.line']
        rule_ranges = range_obj.search([('goal_id', 'in', self.ids)])
        if rule_ranges:
            raise Warning(_("¡Está tratando de eliminar un objetivo especifico que aun está siendo usado!"))
        return super(CustomGoals, self).unlink()

# objetivos personales
class CustomPersonalGoals (models.Model):
    _name="custom.personal.goals"
    _description = "Objetivo personal"

    inverse = fields.Char(string="Inverso")
    name = fields.Char(string='Nombre')
    main_personal_goal_id = fields.Many2one('custom.personal.main.goals',string="Objetivo personal general")
    scope = fields.Char(string='% Alcanzado')
    date = fields.Date(string="Fecha de compromiso")
    comments = fields.Text(string="Comentarios")
    sequence = fields.Integer(string="Secuencia")
    custom_performance_id = fields.Many2one('custom.performance',string="conexión")

# objetivos personales generales
class CustomPersonalMainGoals (models.Model):
    _name="custom.personal.main.goals"
    _description = "Objetivo personal general"

    name = fields.Char(string='Nombre')

    @api.multi
    def unlink(self):
        range_obj = self.env['custom.personal.goals']
        rule_ranges = range_obj.search([('main_personal_goal_id', 'in', self.ids)])
        if len(rule_ranges) > 1:
            raise Warning(_("¡Está tratando de eliminar un objetivo personal general que aun está siendo usado!"))
        return super(CustomPersonalMainGoals, self).unlink()