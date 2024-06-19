# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError

class NegblaSaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    by_promo_line  = fields.Integer(string="Por Promocion")
    programas_ids = fields.Many2many('coupon.program', string="Desc por ")
