# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.tools import float_is_zero
from odoo.tools import safe_eval
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit= "product.template"

    returnable = fields.Boolean(string="Retornable")
    returnable_related_id = fields.Many2one('product.template',string="Retornable relacionado",domain=[('returnable','=',True)])
