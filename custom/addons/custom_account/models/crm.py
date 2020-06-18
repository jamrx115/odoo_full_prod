# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, tools
import logging
import pytz
import re

_logger = logging.getLogger(__name__)

# -- clases y funciones nuevas
class custom_crm_lead (models.Model):
    _inherit = 'crm.lead'

    # modificaciones

    # nuevos campos y metodos
    @api.model
    def create(self, vals):
        if vals.get('stage_id'):
            name = self.env['crm.stage'].browse(vals.get('stage_id')).name
        else:
            name = self.env['crm.stage'].search([], order = 'sequence', limit=1).name
        vals['stage_name'] = name
        return super(custom_crm_lead, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(custom_crm_lead, self).write(vals)
        if vals.get('stage_id'):
            name = self.env['crm.stage'].browse(vals.get('stage_id')).name
            self.write({'stage_name':name})

    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env['res.company']._get_user_currency())
    stage_name = fields.Char('Nombre etapa')
    legalization_code = fields.Char('Número de contrato/OT')
    offer_code = fields.Char('Código de Oferta')
