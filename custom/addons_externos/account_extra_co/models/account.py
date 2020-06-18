# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import openerp.addons.decimal_precision as dp

import sys
#reload(sys)
#sys.setdefaultencoding('UTF8')    


class account_account(models.Model):
  _name = 'account.account'
  _inherit = 'account.account'

  analytic_required = fields.Boolean('Requiere cuenta analitica', help='Indica si la cuenta requiere cuenta analitica o centro de costo', default=False)
  partner_required = fields.Boolean('Requiere tercero', help='Indica si la cuenta requiere tercero', default=False)
  base_required = fields.Boolean('Requiere base', help='Indica si la cuenta requiere base', default=False)

# class account_invoice_line(models.Model):
# 	_name = 'account.invoice.line'
# 	_inherit = 'account.invoice.line'
	
# 	@api.multi
# 	def _check_account_analytic(self):
#             account = self.env['account.account'].browse(self.account_id.id)

#             if (not self.account_analytic_id) and account.analytic_required:            
#                raise ValidationError(_('La cuenta "%s" requiere centro de costo!') % (account.code))	       
#                return False
#             return True
            				
# 	_constraints = [
#               (_check_account_analytic, 'Error!\nLa cuenta contable requiere cuenta analítica.', ['account_id','analytic_account_id']),
#         ]

# class account_invoice_tax(models.Model):
#   _name = 'account.invoice.tax'
#   _inherit = 'account.invoice.tax'
	
#   @api.multi
#   def _check_account_analytic(self):
#             account = self.env['account.account'].browse(self.account_id.id)
         
#             if not self.account_analytic_id  and account.analytic_required:
#                raise ValidationError(_('Error de configuración!'),_('La cuenta "%s" requiere cuenta analitica!') % (account.code))	       
#                return False
#             return True

#   @api.multi
#   def _check_base(self):
#             account = self.env['account.account'].browse(self.account_id.id)
#             print ('cuenta ',account.code)            
#             print ('requiere ',account.base_required)

#             if self.base == 0.00  and account.base_required:
#                raise ValidationError(_('Error de configuración!------'),_('La cuenta "%s" requiere base!') % (account.code))
#                return False
#             return True
		
#   _constraints = [
#               (_check_account_analytic, 'Error!\nLa cuenta contable requiere cuenta analítica.', ['account_id','analytic_account_id']),
#               (_check_base, 'Error!\nLa cuenta contable requiere base de impuesto.', ['account_id']),
#         ]

    
class account_move_line(models.Model):
    _inherit = 'account.move.line'

    tax_amount = fields.Monetary(string="Base impuesto", currency_field='company_currency_id')


    # @api.multi	
    # def _check_account_analytic(self):
    #         account = self.env['account.account'].browse(self.account_id.id)
            
    #         if not self.analytic_account_id  and account.analytic_required:
    #            raise ValidationError(_('La cuenta "%s" requiere centro de costo!') % (account.code))	       
    #            return False

    #         #Valida que el centro de costo no se vista o mayor
    #         if self.analytic_account_id  and self.analytic_account_id.type == 'view':
    #            raise ValidationError(_('El centro de costo "%s" no puede ser vista o mayor!') % (self.analytic_account_id.name))	       
    #            return False

    #         return True

    # @api.multi	
    # def _check_account(self):
    #         account = self.env['account.account'].browse(self.account_id.id)
            
    #         if account.internal_type == 'view':
    #            raise ValidationError(_('La cuenta "%s" no puede ser mayor!') % (account.code))	       
    #            return False

    #         return True

    # @api.multi
    # def _check_partner(self):
    #         account = self.env['account.account'].browse(self.account_id.id)

    #         if not self.partner_id  and account.partner_required:
    #            raise ValidationError(_('La cuenta "%s" requiere tercero!') % (account.code))
    #            return False
    #         return True

    # @api.multi
    # def _check_base(self):
    #         account = self.env['account.account'].browse(self.account_id.id)
    #         if self.tax_base_amount == 0.00  and account.base_required:
    #         #if not self.tax_amount and account.base_required:
    #            raise ValidationError(_('La cuenta "%s" requiere base!***') % (account.code))
    #            return False
    #         return True

    # @api.multi
    # def _check_partner_vat(self):

    #     if self.partner_id and not self.partner_id.ref:
    #            raise ValidationError(_('Tercero: %s') % self.partner_id.name)
    #            return False
    #     return True
		
    # _constraints = [
    #           (_check_account_analytic, 'Error!\nLa cuenta contable requiere cuenta analítica.', ['account_id','analytic_account_id']),
    #           (_check_partner, 'Error!\nLa cuenta contable requiere tercero.', ['account_id','partner_id']),
    #           (_check_base, 'Error!\nLa cuenta contable requiere base de impuesto.', ['account_id','tax_amount','tax_code_id']),
    #           (_check_account, 'Error!\nLa cuenta contable debe ser auxiliar', ['account_id']),
    #           (_check_partner_vat, 'Error!\nEl tercero no tiene un número de identifcación o referencia interna', ['partner_id']),
    #                ]

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def _check_ref_move(self):

     #Busca comprobantes con la misma referencia
     if self.ref and self.journal_id and self.partner_id and self.date:
        move_ids = self.search([('ref','=',self.ref),('journal_id','=',self.journal_id.id),('partner_id','=',self.partner_id.id),('id','!=',self.id),('date','=',self.date)])

        if move_ids:
               raise ValidationError(_('Referenia: %s \nComprobante: %s \nTercero: %s \nFecha: %s') % (self.ref, self.journal_id.name, self.partner_id.name, self.date))
               return False
        return True
		
     _constraints = [
                    (_check_ref_move, 'Error!\nNo se permite contabilizar la misma referencia con el mismo tipo de comprobante tercero y fecha', ['ref','journal_id','partner_id','date']),
                   ]

    @api.multi
    def _check_lock_date(self):
  
        for move in self:
            print('move ',move.name)
            lock_date = max(move.company_id.period_lock_date or '0000-00-00', move.company_id.fiscalyear_lock_date or '0000-00-00')
            if self.user_has_groups('account.group_account_manager'):
                lock_date = move.company_id.fiscalyear_lock_date

            if move.date <= (lock_date or '0000-00-00'):
                #Si es una factura y si a va cambiar el full_reconcile_id no se valida
                is_invoice = False
                for line in move.line_ids:
                    if line.invoice_id and line.full_reconcile_id:
                       is_invoice = True
                    
                if not is_invoice:   
                   if self.user_has_groups('account.group_account_manager'):
                      message = _("You cannot add/modify entries prior to and inclusive of the lock date %s") % (lock_date)
                   else:
                      message = _("You cannot add/modify entries prior to and inclusive of the lock date %s. Check the company settings or ask someone with the 'Adviser' role") % (lock_date)
                   raise UserError(message)
        return True    


# class account_payment(models.Model):
#     _name = 'account.payment'
#     _inherit = 'account.payment'	

#     @api.multi	
#     def _check_account_analytic(self):
#         account = self.env['account.account'].browse(self.account_id.id)

#         if not self.account_id  and account.analytic_required:
#            raise ValidationError(_('Error de configuración!'),_('La cuenta "%s" requiere centro de costo!') % (account.code))
#            return False
#         return True
		
#     _constraints = [
#               (_check_account_analytic, 'Error!\nLa cuenta contable requiere cuenta analitica.', ['account_id','analytic_id']),
#         ]


class account_jurnal(models.Model):
    _name = "account.journal"
    _inherit = "account.journal"
    
    # resolution_number = fields.Char('Número de Resolución')
    # number_from = fields.Integer('Desde')
    # number_to = fields.Integer('Hasta')
    # expedition_date = fields.Date('Fecha De Expedición')
    type = fields.Selection([
            ('sale', 'Sale'),
            ('purchase', 'Purchase'),
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('general', 'Miscellaneous'),
            ('apertura', 'Apertura'),
            ('cierre', 'Cierre'),
        ], required=True,
        help="Select 'Sale' for customer invoices journals.\n"\
        "Select 'Purchase' for vendor bills journals.\n"\
        "Select 'Cash' or 'Bank' for journals that are used in customer or vendor payments.\n"\
        "Select 'General' for miscellaneous operations journals.")


