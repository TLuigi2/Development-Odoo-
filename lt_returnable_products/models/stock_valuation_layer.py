# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import float_is_zero
from odoo.tools import safe_eval
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockValuationLayer(models.Model):
    _inherit= "stock.valuation.layer"

    partner_id = fields.Many2one('res.partner',string="Proveedor")
    retornable = fields.Boolean(string="Producto retornable",related="product_id.returnable")