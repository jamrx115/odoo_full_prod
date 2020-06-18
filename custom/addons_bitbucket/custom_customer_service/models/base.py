# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime

import logging
import re

_logger = logging.getLogger(__name__)

# peticiones, quejas, reclamos y sugerencias
class CustomClaim (models.Model):
    _name = "custom.claim"
    _description = "PQRS"

    name = fields.Char(string="Nombre", required=True)
    date = fields.Date(string="Fecha")
    description = fields.Text('Descripción')
    