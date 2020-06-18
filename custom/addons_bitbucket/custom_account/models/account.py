# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, tools
import logging
import pytz
import re

_logger = logging.getLogger(__name__)

# Modificando impuestos
class AccountTaxUpdated(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _getfilter_accounts(self):
        return ['&', ('deprecated', '=', False),
        		('user_type_id', '!=', 
        		self.env['account.account.type'].search([('name','=','Vista')]).id)]

    account_id = fields.Many2one('account.account', domain=_getfilter_accounts, string='Cuenta de impuestos en facturas', ondelete='restrict',
        help="Cuenta que se establecerá en las líneas de impuestos de facturas.", oldname='account_collected_id')
    refund_account_id = fields.Many2one('account.account', domain=_getfilter_accounts, string='Cuenta de impuestos en notas crédito', ondelete='restrict',
        help="Cuenta que se establecerá en las líneas de impuestos de notas crédito.", oldname='account_paid_id')

# Resoluciones en Diarios
class AccountResolution(models.Model):
    _name = "custom.resol"
    _description = "Resoluciones"

    journal_id = fields.Many2one('account.journal', string="Diario")
    name  = fields.Char('Resolución')
    sel_type = fields.Selection([
        ('por computador', 'Por computador'),
        ('electronica', 'Electrónica')
    ], string='Tipo', default='por computador')
    date_resol = fields.Date('Fecha resolución')
    int_startr = fields.Integer('Inicia resolución')
    int_endres = fields.Integer('Fin resolución')

# Actualización de Diarios
class AccountJournalUpdated(models.Model):
    _inherit = 'account.journal'

    str_footer = fields.Char('Pie de página')
    resols = fields.One2many('custom.resol', 'journal_id', string="Resoluciones")
