# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools
import logging

_logger = logging.getLogger(__name__)

# Clase que gestiona los códigos de puestos de trabajo
# class JobCode(models.Model):
    # _inherit = 'hr.job'
    # _sql_constraints = [
        # ('job_code_unique', 'UNIQUE(x_code)', 'El código ingresado ya fue asignado')
    # ]

# Clase que actualiza responsables con cambio de jefe
class DepartmentResponsable(models.Model):
    _inherit = 'hr.department'

    @api.multi
    @api.onchange('manager_id')
    def _onchange_manager_id(self):
        old_manager = self._origin.manager_id
        new_manager = self.manager_id

        # 1. Reiniciando Jefes involucrados
        new_manager.write({'parent_id': None})
        old_manager.write({'parent_id': None})

        # 2. Actualizando antiguo jefe
        old_manager.write({'parent_id': new_manager.id})

        # 3. Actualizando nuevo jefe
        if self.parent_id:
            new_parent = self.parent_id.manager_id
            new_manager.write({'parent_id': new_parent.id})

        # 4. Actualizando subordinados
        employees = self.env['hr.employee'].search([['parent_id', '=', old_manager.id]])
        for e in employees:
            e.parent_id = new_manager.id
            