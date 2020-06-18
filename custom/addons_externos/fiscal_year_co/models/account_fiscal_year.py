# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright (C) Innovatecsa SAS
# Authors       Over Garcia Caballero, gerencia@innovatecsa.com
#    

from datetime import datetime
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp

class account_fiscalyear(models.Model):
    _name = "account.fiscalyear"
    _description = "Fiscal Year"
    

    name = fields.Char('Nombre', required=True)
    code = fields.Char('Codigo', size=6, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)
    date_start = fields.Date('Fecha inicio', required=True)
    date_stop = fields.Date('Fecha final', required=True)
    state =  fields.Selection([('draft','Abierto'), ('done','Cerrado')], 'Estado', readonly=True, copy=False,default='draft')

    _order = "date_start, id"

    @api.multi
    def _check_duration(self):
        obj_fy = self
        if obj_fy.date_stop < obj_fy.date_start:
            return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe start date of a fiscal year must precede its end date.', ['date_start','date_stop'])
    ]


    def find(self, dt=None, exception=True):
        res = self.finds(dt, exception)
        return res and res[0] or False

    def finds(self, dt=None, exception=True):
        if not dt:
            dt = fields.Date.context_today(self)
        args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]
        
        if self._context.get('company_id', False):
            company_id = self._context['company_id']
        else:
            company_id = self.env['res.users'].browse(self._uid).company_id.id
            
        #print ('dt ',dt)    
        #print ('company_id ',company_id)    
            
        args.append(('company_id', '=', company_id))
        ids = self.search(args)
        if not ids:
           raise ValidationError(_('No existe periodo fiscal abierto para la fecha %s') % dt)
           
        return ids


class AccountAccount(models.Model):
    _inherit = "account.account"

    parent_id = fields.Many2one('account.account', 'Cta. mayor', ondelete='cascade', domain=[('user_type_id.type','=','view')])
    child_parent_ids = fields.One2many('account.account','parent_id','Ctas. hijas')

    @api.multi
    def _check_allow_type_change(self, new_type):
        restricted_groups = ['consolidation','view']
        line_obj = self.env['account.move.line']
        for account in self:
            old_type = account.internal_type
            #account_ids = self.search([('id', 'child_of', [account.id])])
            #if line_obj.search([('account_id', 'in', account_ids.ids)]):
            if line_obj.search([('account_id', '=', account.id)]):
                if (new_type in restricted_groups):
                    raise ValidationError(_('No puede cambiar el tipo en la cuenta contable "%s" si contiene movimientos contables') % (account.code)) 

    @api.multi
    def write(self, vals):
        if 'user_type_id' in vals.keys():
            type_id = self.env['account.account.type'].browse(vals['user_type_id'])
            self._check_allow_type_change(type_id.type)

        return super(AccountAccount, self).write(vals)


class account_analytic_account(models.Model):
    _name = "account.analytic.account"
    _inherit = "account.analytic.account"

    type = fields.Selection([('view','Vista'), ('normal','Centro de costo'),('contract','Contrato or Proyecto'),('template','Plantilla de contrato')], 'Tipo de cuenta', required=True, default = 'contract')
    parent_id = fields.Many2one('account.analytic.account', 'Padre', ondelete='cascade', domain=[('type','=','view')])
    child_ids = fields.One2many('account.analytic.account', 'parent_id', 'Cuentas hijas', copy=True)

    @api.multi
    def _check_allow_type_change(self, new_type):
        restricted_groups = ['template','view']
        line_obj = self.env['account.move.line']
        for account in self:
            old_type = account.type
            account_ids = self.search([('id', 'child_of', [account.id])])
            if line_obj.search([('analytic_account_id', 'in', account_ids.ids)]):
                if (new_type in restricted_groups):
                    raise ValidationError(_('No puede cambiar el tipo en la cuenta analítica "%s" si contiene movimientos contables') % (account.name)) 

    @api.multi
    def write(self, vals):
        print('vals',vals)
        if 'type' in vals.keys():
            self._check_allow_type_change(vals['type'])

        return super(account_analytic_account, self).write(vals)

class AccountAccountType(models.Model):
    _name = "account.account.type"
    _inherit = "account.account.type"

    type = fields.Selection([
        ('other', 'Regular'),
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
        ('liquidity', 'Liquidity'),
        ('view', 'Vista'),
    ], required=True, default='other',
        help="The 'Internal Type' is used for features available on "\
        "different types of accounts: liquidity type is for cash or bank accounts"\
        ", payable/receivable is for vendor/customer accounts.")
        
    close_method = fields.Selection([('none', 'None'), ('balance', 'Balance'), ('detail', 'Detail'), ('unreconciled', 'Unreconciled')], 'Metodo de cierre', required=True, default='none',
                  help="""Set here the method that will be used to generate the end of year journal entries for all the accounts of this type.
                       'None' means that nothing will be done.
                       'Balance' will generally be used for cash accounts.
                       'Detail' will copy each existing journal item of the previous year, even the reconciled ones.
                       'Unreconciled' will copy only the journal items that were unreconciled on the first day of the new fiscal year.""")

    @api.multi
    def get_default_account_close_method(self):
        acc_type_obj = self.env['account.account.type']
        ids = acc_type_obj.search([])
        res = acc_type_obj.browse(ids)
        result = []
        for rec in res:
            if   rec.name == 'Vista':
                 close_method = 'none'
            elif rec.name == 'Por Cobrar':
                 close_method = 'unreconciled'
            elif rec.name == 'Por pagar':
                 close_method = 'unreconciled'
            elif rec.name == 'Banco y caja':
                 close_method = 'balance'
            elif rec.name == 'Activos Corrientes':
                 close_method = 'balance'
            elif rec.name == 'Activos no-corrientes':
                 close_method = 'balance'
            elif rec.name == 'Pre-pagos':
                 close_method = 'balance'
            elif rec.name == 'Activos fijos':
                 close_method = 'balance'
            elif rec.name == 'Pasivos Corrientes':
                 close_method = 'balance'
            elif rec.name == 'Pasivos no-corrientes':
                 close_method = 'balance'
            elif rec.name == 'Patrimonio':
                 close_method = 'balance'
            elif rec.name == 'Ganancias del Ano Actual':
                 close_method = 'balance'
            elif rec.name == 'Otro Ingreso':
                 close_method = 'none'
            elif rec.name == 'Ingreso':
                 close_method = 'none'
            elif rec.name == 'Amortizacion':
                 close_method = 'balance'
            elif rec.name == 'Gastos':
                 close_method = 'none'
            elif rec.name == 'Costos Directos':
                 close_method = 'none'
            else :
                 close_method = 'none'
            acc_type_obj.write(rec.id,{'close_method':close_method})
