# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import float_is_zero
from odoo.tools import safe_eval
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockMove(models.Model):
    _inherit= "stock.move"

    def _prepare_common_svl_vals(self):
        """Cuando se crea un `stock.valuation.layer` a partir de un `stock.move`, podemos preparar un dict de
        valores comunes se agrego el proveedor en esta funcion

        :retorna: los valores comunes al crear un `stock.valuation.layer` a partir de un `stock.move`
        :rtype: dictado
        """
        self.ensure_one()
        return {
            'partner_id':self.picking_id.partner_id.id or False,
            'stock_move_id': self.id,
            'company_id': self.company_id.id,
            'product_id': self.product_id.id,
            'description': self.reference and '%s - %s' % (self.reference, self.product_id.name) or self.product_id.name,
        }
     