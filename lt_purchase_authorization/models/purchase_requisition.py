# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.tools import float_is_zero
from odoo.tools import safe_eval
from odoo import api, exceptions, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang, get_lang, format_amount

class PurchaseRequisition(models.Model):

    _inherit = 'purchase.requisition'

    department = fields.Many2one('hr.department',string="Departamento")
    type_purchase = fields.Selection(selection=[('Directa','Directa'),('Indirecta','Indirecta')], string="Tipo Compra", default="Indirecta")