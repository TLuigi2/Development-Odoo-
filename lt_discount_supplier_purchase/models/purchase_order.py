# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.tools import float_is_zero
from odoo.tools import safe_eval
from odoo import api, exceptions, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang, get_lang, format_amount

class PurchaseOrder(models.Model):
    _inherit= "purchase.order"

    total_original = fields.Monetary(string='Total original', store=True, readonly=True, compute='_amount_all')

    @api.depends('order_line.price_total','order_line.price_total_new')
    def _amount_all(self):
        '''
        Recalculo de la funcion agregando el campo total_with_discount
        '''
        for order in self:
            amount_untaxed = amount_tax = amount_discount = 0.0
            for line in order.order_line:
                line._compute_amount()
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amount_discount += line.price_total_new
            currency = order.currency_id or order.partner_id.property_purchase_currency_id or self.env.company.currency_id
            order.update({
                'amount_untaxed': currency.round(amount_untaxed),
                'amount_tax': currency.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'total_original': amount_discount,
            })


    def _prepare_picking(self):
        '''
        Traspaso a movimiento de entrada del valor total inventario desde la orden de compra
        '''
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
                })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s", self.partner_id.name))
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'user_id': False,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
            'total_with_discount':self.amount_untaxed
            }


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        '''
        Llenado automatico de descuentos relacionados al proveedor en las lineas de la orden de compra
        '''
        if self.partner_id:
            if self.order_line:
                for line in self.order_line:
                    line.discount_1 = self.partner_id.discount_1
                    line.discount_2 = self.partner_id.discount_2
                    line.discount_3 = self.partner_id.discount_3
                    line.discount_4 = self.partner_id.discount_4
                    line.onchange_discounts()
                    line._compute_amount()
            self._amount_all()


    def _add_supplier_to_product(self):
        '''
        Cambiar price_unit a price_unit_new
        '''
        for line in self.order_line:
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            already_seller = (partner | self.partner_id) & line.product_id.seller_ids.mapped('name')
            if line.product_id and not already_seller and len(line.product_id.seller_ids) <= 10:
                currency = partner.property_purchase_currency_id or self.env.company.currency_id
                #Moficicacion obtencion de precio
                #price = self.currency_id._convert(line.price_unit, currency, line.company_id, line.date_order or fields.Date.today(), round=False)
                price = self.currency_id._convert(line.price_unit_new, currency, line.company_id, line.date_order or fields.Date.today(), round=False)
                if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
                    default_uom = line.product_id.product_tmpl_id.uom_po_id
                    price = line.product_uom._compute_price(price, default_uom)

                supplierinfo = self._prepare_supplier_info(partner, line, price, currency)

                seller = line.product_id._select_seller(
                    partner_id=line.partner_id,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date(),
                    uom_id=line.product_uom)
                if seller:
                    supplierinfo['product_name'] = seller.product_name
                    supplierinfo['product_code'] = seller.product_code
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                try:
                    line.product_id.write(vals)
                except AccessError: 
                    break


class PurchaseOrderLine(models.Model):
    _inherit= "purchase.order.line" 

    price_unit_new = fields.Monetary(string="Nuevo precio unitario")
    price_total_new = fields.Monetary(compute='_compute_amount', string='Precio total nuevo', store=True)
    discount_1 = fields.Integer(string="Desc 1(%)")
    discount_2 = fields.Integer(string="Desc 2(%)")
    discount_3 = fields.Integer(string="Desc 3(%)")
    discount_4 = fields.Float(string="Desc 4($)")

    @api.onchange('product_id')
    def onchange_products(self):
        '''
        Llenado automatico de valores de descuento al modificar o agregar un producto
        '''
        if self.product_id and self.order_id.partner_id:
            self.discount_1 = self.order_id.partner_id.discount_1
            self.discount_2 = self.order_id.partner_id.discount_2
            self.discount_3 = self.order_id.partner_id.discount_3
            self.discount_4 = self.order_id.partner_id.discount_4

    @api.depends('product_qty', 'price_unit', 'taxes_id','price_unit_new')
    def _compute_amount(self):

        '''
        Calcula total por partida con impuestos
        '''
        for line in self:
            taxes = line.taxes_id.compute_all(**line._prepare_compute_all_values())
            taxes_new = line.taxes_id.compute_all(**line._prepare_compute_all_values_discount())
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'price_total_new': taxes_new['total_included']
            })

    def _prepare_compute_all_values_discount(self):
        '''
        Calculo del valor con impuestos sobre la cantidad generada al calculo de valor inventario
        '''
        self.ensure_one()
        return {
            'price_unit': self.price_unit_new,
            'currency': self.order_id.currency_id,
            'quantity': self.product_qty,
            'product': self.product_id,
            'partner': self.order_id.partner_id,
        }

    @api.onchange('discount_1','discount_2','discount_3','discount_4','price_unit_new','product_qty','taxes_id')
    def onchange_discounts(self):
        '''
        Funcion para calcular el monto subtotal con descuentos
        '''
        if self.product_id:
            amount_discount = self.price_unit_new
            self.price_unit  = amount_discount
            if self.discount_1 > 0 and self.price_unit_new > 0:
                amount_discount = amount_discount - (amount_discount * (self.discount_1/100))
                self.price_unit  = amount_discount
            
            if self.discount_2 > 0 and self.price_unit_new > 0:
                amount_discount = amount_discount - (amount_discount * (self.discount_2/100))
                self.price_unit  = amount_discount

            if self.discount_3 > 0 and self.price_unit_new > 0:
                amount_discount = amount_discount - (amount_discount * (self.discount_3/100))
                self.price_unit  = amount_discount

            if self.discount_4 > 0 and self.price_unit_new > 0:
                self.price_unit = self.price_unit - self.discount_4



    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom,price_subtotal):
        """ Llenado de  diccionario listo para ser usado en stock.move's create()
        """
        self.ensure_one()
        self._check_orderpoint_picking_type()
        product = self.product_id.with_context(lang=self.order_id.dest_address_id.lang or self.env.user.lang)
        date_planned = self.date_planned or self.order_id.date_planned
        return {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.product_id.display_name or '')[:2000],
            'product_id': self.product_id.id,
            'date': date_planned,
            'date_deadline': date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': (self.orderpoint_id and not (self.move_ids | self.move_dest_ids)) and self.orderpoint_id.location_id.id or self.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'description_picking': product.description_pickingin or self.name,
            'propagate_cancel': self.propagate_cancel,
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
            'product_uom_qty': product_uom_qty,
            'product_uom': product_uom.id,
            'product_packaging_id': self.product_packaging_id.id,
            'sequence': self.sequence,
            'total_with_discount':self.price_subtotal
        }

    def _prepare_stock_moves(self, picking):
        """ Prepara los datos de movimiento de existencias para una línea de pedido. Esta función devuelve una lista de
        diccionario listo para ser usado en stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res

        price_unit = self._get_stock_move_price_unit()
        qty = self._get_qty_procurement()
        total_with_discount = self.price_subtotal

        move_dests = self.move_dest_ids
        if not move_dests:
            move_dests = self.move_ids.move_dest_ids.filtered(lambda m: m.state != 'cancel' and not m.location_dest_id.usage == 'supplier')

        if not move_dests:
            qty_to_attach = 0
            qty_to_push = self.product_qty - qty
        else:
            move_dests_initial_demand = self.product_id.uom_id._compute_quantity(
                sum(move_dests.filtered(lambda m: m.state != 'cancel' and not m.location_dest_id.usage == 'supplier').mapped('product_qty')),
                self.product_uom, rounding_method='HALF-UP')
            qty_to_attach = move_dests_initial_demand - qty
            qty_to_push = self.product_qty - move_dests_initial_demand

        if float_compare(qty_to_attach, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(qty_to_attach, self.product_id.uom_id)
            res.append(self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom,total_with_discount))
        if not float_is_zero(qty_to_push, precision_rounding=self.product_uom.rounding):
            product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(qty_to_push, self.product_id.uom_id)
            extra_move_vals = self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom,total_with_discount)
            extra_move_vals['move_dest_ids'] = False  # don't attach
            res.append(extra_move_vals)
        return res

    def _prepare_account_move_line(self, move=False):
        """ Se preparan los datos a enviar para generar factura considerando los cambios de descuentos que provienen desde la orden de compra y manda los valores en account.move.line's create()
        """
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'price_unit': self.currency_id._convert(self.price_unit_new, aml_currency, self.company_id, date, round=False),
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'analytic_account_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'purchase_line_id': self.id,
        }
        if not move:
            return res

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id,
        })
        return res

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        """ Se preparan los datos para llenar por defecto los valores en purchase.order.line
        """
        if not self.product_id or self.invoice_lines:
            return
        params = {'order_id': self.order_id}
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
            params=params)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # If not seller, use the standard price. It needs a proper currency conversion.
        if not seller:
            po_line_uom = self.product_uom or self.product_id.uom_po_id
            price_unit = self.env['account.tax']._fix_tax_included_price_company(
                self.product_id.uom_id._compute_price(self.product_id.standard_price, po_line_uom),
                self.product_id.supplier_taxes_id,
                self.taxes_id,
                self.company_id,
            )
            if price_unit and self.order_id.currency_id and self.order_id.company_id.currency_id != self.order_id.currency_id:
                price_unit = self.order_id.company_id.currency_id._convert(
                    price_unit,
                    self.order_id.currency_id,
                    self.order_id.company_id,
                    self.date_order or fields.Date.today(),
                )

            self.price_unit = price_unit
            return

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, self.product_id.supplier_taxes_id, self.taxes_id, self.company_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, self.order_id.currency_id, self.order_id.company_id, self.date_order or fields.Date.today())

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

        self.price_unit_new = price_unit

        default_names = []
        vendors = self.product_id._prepare_sellers({})
        for vendor in vendors:
            product_ctx = {'seller_id': vendor.id, 'lang': get_lang(self.env, self.partner_id.lang).code}
            default_names.append(self._get_product_purchase_description(self.product_id.with_context(product_ctx)))

        if (self.name in default_names or not self.name):
            product_ctx = {'seller_id': seller.id, 'lang': get_lang(self.env, self.partner_id.lang).code}
            self.name = self._get_product_purchase_description(self.product_id.with_context(product_ctx))