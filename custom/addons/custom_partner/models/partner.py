# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, tools
from odoo.exceptions import UserError
import logging
import pytz
import re

_logger = logging.getLogger(__name__)

# Personalizacion campos OPenSOft
class ResPartnerCustomOpenSoft(models.Model):
    _inherit = 'res.partner'

    vat_ref = fields.Char('NIT Completo', compute="_compute_nit_information",
        store=True, readonly=True)
    vat_vd = fields.Integer(string="Digito Verificación", compute="_compute_nit_information", 
        store=True, readonly=True)
    # eliminando required
    vat_type = fields.Selection(
        string=u'Tipo de Documento',
        selection=[
            ('11', '11 - Registro civil de nacimiento'),
            ('12', '12 - Tarjeta de identidad'),
            ('13', u'13 - Cédula de ciudadanía'),
            ('14', '14 - Certificado de la Registraduría para sucesiones ilíquidas de personas naturales que no tienen ningún documento de identificación.'),
            ('15', '15 - Tipo de documento que identifica una sucesión ilíquida, expedido por la notaria o por un juzgado. '),
            ('21', '21 - Tarjeta de extranjería'),
            ('22', '22 - Cédula de extranjería'),
            ('31', '31 - NIT/RUT'),
            ('33', '33 - Identificación de extranjeros diferente al NIT asignado DIAN'),
            ('41', '41 - Pasaporte'),
            ('42', '42 - Documento de identificación extranjero'),
            ('43', '43 - Sin identificación del exterior o para uso definido por la DIAN'),
        ],
        required=False,
        help = 'Identificacion del Cliente, segun los tipos definidos por la DIAN.',
    )
    ciiu_id = fields.Many2one(
        string='Actividad CIIU',
        comodel_name='res.ciiu',
        domain=[('type', '!=', 'view')],
        help=u'Código industrial internacional uniforme (CIIU)',
        required=False
    )

    def check_vat_dv(self):
        pass

    def _compute_vat_ref(self):
        pass

    @api.depends('vat')
    def _compute_nit_information(self):
        for record in self:
            colombia = record.env['res.country'].search([['name', '=', 'Colombia']])
            if record.vat:
                if record.country_id == colombia:
                    if record.vat.isdigit():
                        cantidad_ceros = 15-len(record.vat)
                        string_base = str(0)*cantidad_ceros+str(record.vat)
                        base = [int(string_base[14:15]), int(string_base[13:14]), int(string_base[12:13]),
                                int(string_base[11:12]), int(string_base[10:11]), int(string_base[9:10]),
                                int(string_base[8:9]), int(string_base[7:8]), int(string_base[6:7]),
                                int(string_base[5:6]), int(string_base[4:5]), int(string_base[3:4]),
                                int(string_base[2:3]), int(string_base[1:2]), int(string_base[0:1])]
                        auxiliar_base =  base[0]*3 + base[1]*7 + base[2]*13 
                        auxiliar_base += base[3]*17 + base[4]*19 + base[5]*23
                        auxiliar_base += base[6]*29 + base[7]*37 + base[8]*41 
                        auxiliar_base += base[9]*43 + base[10]*47 + base[11]*53
                        auxiliar_base += base[12]*59 + base[13]*67 + base[14]*71
                        auxiliar = auxiliar_base % 11
                        if auxiliar == 0:
                            record.vat_vd = 0
                        elif auxiliar == 1:
                            record.vat_vd = 1
                        else:
                            record.vat_vd = 11-auxiliar
                        # guardando el campo NIT
                        record.vat_ref = str(record.vat)+'-'+str(record.vat_vd)
                    else:
                        raise UserError('En Colombia los NIT deben ser numéricos')
                else:
                    record.vat_vd  = 0
                    record.vat_ref = record.vat
    
    def check_vat_co(self, vat, vat_vd):
        pass

# Modelo nuevo para fechas importantes - solo para contactos
class ResPartnerDatesImportant(models.Model):
    _name="partner.dates.important"
    _description= "Fechas importantes"

    contact_id = fields.Many2one('res.partner', string='Contacto', required=True)
    type = fields.Selection([
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('other', 'Other')
    ], string='Tipo', default='single')
    date = fields.Date(string='Fecha', index=True)
    description = fields.Char('Descripción')

# Modelo nuevo para area del contacto - solo para contactos
class CustomContactArea(models.Model):
    _name = "custom.contact.area"
    _description = "Area de Contacto"
    _inherit = ['mail.thread']

    name = fields.Char(string="Area de Contacto", track_visibility='onchange')

# Personalizacion modelo tarjetas de contacto 
class ResPartnerCustomPartner(models.Model):
    _inherit = 'res.partner'

    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Estado civil', default='single')
    profession = fields.Char('Profesión')
    likes = fields.Text(string='Hobbies y Gustos', help="Hobbies(Billar, ajedrez, baile, pesca, etc) y Gustos (musicales, de licor, de comida)")
    birthday = fields.Date(string='Cumpleaños', index=True)
    date_ids = fields.One2many('partner.dates.important', 'contact_id', 'Fechas importantes')

    # eliminando required
    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
        string="Cuenta por cobrar", oldname="property_account_receivable",
        domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
        required=False)
    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
        string="Cuenta por pagar", oldname="property_account_payable",
        domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
        required=False)

    @api.model
    def create(self, vals):
        # EL nit incluído el dígito de verificación será considerado la referencia interna del contacto
        if vals.get('vat'):
            if vals.get('parent_id') == False:
                vals['ref'] = vals.get('vat_ref')
            else:
                vals['ref'] = self.env['res.partner'].browse(vals.get('parent_id')).vat_ref

        partner = super(ResPartnerCustomPartner, self).create(vals)
        return partner

    @api.multi
    def write(self, vals):
        parent = self.env['res.partner'].browse(self.parent_id.id)
        if parent.id:
            vals['ref'] = parent.vat_ref
        else:
            vals['ref'] = self.vat_ref
        return super(ResPartnerCustomPartner, self).write(vals)
