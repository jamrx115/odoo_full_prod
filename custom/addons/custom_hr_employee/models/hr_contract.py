# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, tools
import logging
import pytz
import re

_logger = logging.getLogger(__name__)

# Nuevo modelo para novedades administrativas
class TipoNovedadContrato (models.Model):
    _name="custom.tipo.novedad.contrato"
    _description= "Tipo novedad contrato"

    name = fields.Char(string='Descripción', copy=False)

class HrContractNewFields(models.Model):
    _inherit = 'hr.contract'

    x_numero_contrato = fields.Char(string='Identificador Contrato Físico')

    x_tipo_novedad_contrato_id = fields.Many2one('custom.tipo.novedad.contrato', string='Tipo novedad creacion del contrato', required=True)
    x_tipo_novedad_cierre_contrato_id = fields.Many2one('custom.tipo.novedad.contrato', string='Tipo novedad cierre del contrato')
    
    x_annual_holiday = fields.Integer('Días vacaciones anuales', default = 15, 
        help='Vacaciones para contrato laboral')
    x_annual_familydays = fields.Integer('Días libres familiares anuales', default = 2, 
        help='Ley 1857 del 26 julio del 2017')

    x_medic_pre = fields.Boolean(string='Adicional por servicios médicos', help='Aplica para salario > 2 SMMLV')
    x_pensi_volu = fields.Boolean(string='Adicional por pensiones voluntarias', help='Aplica para salario >= 1 SMMLV')

class HrContractWageComplements(models.Model):
    _inherit = 'hr.contract'

    # suman
    x_bonificacion = fields.Float(string='Bonificación fija')
    x_comision = fields.Float(string='Comisión fija')
    # restan
    x_medic_prep  = fields.Float(string='Descuento mensual')
    x_pensi_volun = fields.Float(string='Descuento mensual')
    x_seguros = fields.Float(string='Seguros adquiridos')

class HrContractRtefte(models.Model):
    _inherit = 'hr.contract'
    
    x_pagos_alim  = fields.Float(string='Pagos a 3ros por alimentación')
    x_viat_ocasi  = fields.Float(string='Viáticos ocasionales reembolsables')
    x_ahorros_afc = fields.Float(string='Ahorros cuentas AFC')
    x_rentrab_ex  = fields.Float(string='Rentas de trabajo exentas')
    x_int_viviend = fields.Float(string='Intereses en préstamos vivienda')
    x_polizas_seg = fields.Float(string='Pólizas de seguros')

class HrContractUpdated(models.Model):
    _inherit = 'hr.contract'

    @api.model
    def create(self, vals):
    	tipo_novedad_contrato_vinculacion = self.env['custom.tipo.novedad.contrato'].search([('name', 'like', 'Vinculación%')])

    	res = super(HrContractUpdated, self).create(vals)
    	employee_obj = self.env['hr.employee'].search([('id', '=', vals['employee_id'])], limit=1)

    	# escribir el horario en datos de empleado
    	if vals['resource_calendar_id']:
    		self.employee_id.resource_id.write({'calendar_id': self.resource_calendar_id.id})
    	# escribir la fecha de inicio de labores en datos de empleado
    	if vals['date_start']:
    		if vals['x_tipo_novedad_contrato_id'] == tipo_novedad_contrato_vinculacion.id:
    			employee_obj.write({'joining_date': vals['date_start']})

    	return res

    @api.multi
    def write(self, vals):
        tipo_novedad_contrato_vinculacion = self.env['custom.tipo.novedad.contrato'].search([('name', 'like', 'Vinculación%')])
        res = super(HrContractUpdated, self).write(vals)

        for contract_obj in self:
            employee_obj = self.env['hr.employee'].search([('id', '=', contract_obj.employee_id.id)], limit=1)
            # escribir el horario en datos de empleado
            if contract_obj.resource_calendar_id:
                contract_obj.employee_id.resource_id.write({'calendar_id': contract_obj.resource_calendar_id.id})
            # escribir la fecha de inicio de labores en datos de empleado
            if contract_obj.date_start:
                if contract_obj.x_tipo_novedad_contrato_id.id == tipo_novedad_contrato_vinculacion.id:
                    employee_obj.write({'joining_date': contract_obj.date_start})
            return res
