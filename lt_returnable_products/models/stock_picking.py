# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import float_is_zero
from odoo.tools import safe_eval
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit= "stock.picking"

    """
    Modificacion en onchange para agregar en automatico el producto retornable relacionado al producto principal, con la misma cantidad.
    """
    @api.onchange('move_ids_without_package')
    def _onchange_move_ids_without_package(self):
        if self.picking_type_id:
            if self.picking_type_id.code == 'internal':
                for line in self.move_ids_without_package:
                    if line.product_id.returnable_related_id:
                        product = self.env['product.product'].search([('product_tmpl_id', '=', line.product_id.returnable_related_id.id)])
                        new_line = []
                        vals = {
                            'name':product.name,
                            'product_id': product.id,
                            'product_uom_qty': line.product_uom_qty,
                            'product_uom':product.uom_id.id
                        }
                        
                        new_line.append((0, 0, vals))
                        bandera = False
                        for line_new in self.move_ids_without_package:
                            if line_new.product_id.id == product.id:
                                cantidad = 0
                                for line_old in self.move_ids_without_package:
                                    if line_old.product_id.id == line.product_id.id:
                                        cantidad += line_old.product_uom_qty
                                line_new.product_uom_qty = cantidad
                                bandera=True
                        if bandera == False:
                            self.move_ids_without_package = new_line

    """
    Modificacion en onchange para agregar en automatico el producto retornable relacionado al producto principal, con la misma cantidad.
    """
    @api.onchange('move_line_ids_without_package')
    def _onchange_move_line_ids_without_package(self):
        if self.picking_type_id:
            if self.picking_type_id.code == 'internal':
                for line in self.move_line_ids_without_package:
                    if line.product_id.returnable_related_id:
                        product = self.env['product.product'].search([('product_tmpl_id', '=', line.product_id.returnable_related_id.id)])
                        new_line = []
                        vals = {
                            'product_id': product.id,
                            'qty_done': line.qty_done,
                            'product_uom_qty': line.qty_done,
                            'product_uom_id':product.uom_id.id
                        }
                        
                        new_line.append((0, 0, vals))
                        bandera = False
                        for line_new in self.move_line_ids_without_package:
                            if line_new.product_id.id == product.id:
                                cantidad = 0
                                for line_old in self.move_line_ids_without_package:
                                    if line_old.product_id.id == line.product_id.id:
                                        cantidad += line_old.qty_done
                                line_new.qty_done = cantidad
                                bandera=True
                        if bandera == False:
                            self.move_line_ids_without_package = new_line

