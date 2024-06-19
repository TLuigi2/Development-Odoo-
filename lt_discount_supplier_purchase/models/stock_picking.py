# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import float_is_zero
from odoo.tools import safe_eval
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError, ValidationError

class StockPicking(models.Model):
    _inherit= "stock.picking"

    total_with_discount = fields.Float(string="Total con descuento")
