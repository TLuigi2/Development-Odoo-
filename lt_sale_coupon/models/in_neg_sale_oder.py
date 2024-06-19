# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class NegblaSaleOrder(models.Model):
    _inherit = "sale.order"

    verifipromo = fields.Boolean(string="Modificar linea sin buscar promociones", help="Cuando lo active puede modificar la parida sin que odoo agrege mas productos por las promociones sirve para ajustar la cotizacion.")
    acomunlated_points  = fields.Float(string="Puntos Acumulados", copy=False)
    points_use  = fields.Boolean(string="Puntos usados", copy=False)

    @api.onchange('order_line')
    def active_acction_promotion(self):
        '''
        Activa la promociones que con cuerden las lineas y esten activos.
        '''
        for rec in self:
            if rec.verifipromo ==  False:
                count  = 0
                value = False
                #Primero se hace los filtros si aplican con los filtros nativos de odoo 
                programs = rec._get_applicable_programs()
                rec.reset_is_reward_line()
                #rec._remove_program_relation(programs)
                #raise ValidationError(f'PROGRMAS {programs}')
                for pro in programs:
                    if pro.promo_code_usage =='no_code_needed' and pro.promo_applicability == 'on_current_order' and pro.state_coupon_progrm == 'active':
                        
                        if pro.reward_type == 'product':
                            #evaluamos si es uno o varios productos
                            if pro.multi_free_prductos == False:
                                #metodo para devolver cuanas veces cumple la promocion 
                                veces_que_aplica_promo = rec.ony_one_free_product_account_apply(pro)
                                if veces_que_aplica_promo != 0:
                                    values = [rec._values_reward_product_id(pro, veces_que_aplica_promo)]
                            else:
                                #multiples productos
                                veces_que_aplica_promo = rec.ony_one_free_product_account_apply(pro)
                                productos = rec._values_reward_multi_product_id(pro, veces_que_aplica_promo)
                                #raise ValidationError(f'esto es productos {productos}')
                        elif pro.reward_type == 'discount':
                                values = rec._get_reward_values_discount(pro)
                                if pro.discount_apply_on == 'on_order':
                                    rec.discount_in_orden(pro)
                                elif pro.discount_apply_on == 'cheapest_product':
                                    rec.discount_in_cheap_product(pro)
                                elif pro.discount_apply_on == 'specific_products':
                                    rec.discount_in_selection_product(pro)
                        seq = max(rec.order_line.mapped('sequence'), default=10) + 1
                        
                        if pro.multi_free_prductos == False:
                            if value != False:
                                for value in values:
                                    value['sequence'] = seq
                        #validando que solo funcione un vez
                        line_found = False  # Variable de bandera para realizar un seguimiento de si se cumple la condición

                        if pro.reward_type == 'product':
                            rec.no_code_promo_program_ids+=pro #agrega promocion
                            if pro.multi_free_prductos == False:
                                if veces_que_aplica_promo != 0:
                                    for linea in rec.order_line:
                                        if linea.product_id.id == values[0]['product_id'] and linea.price_unit == 0.01:
                                            line_found = True  # Establecer la bandera en True si se cumple la condición
                                            break  # Salir del bucle si se encuentra una línea que cumple la condición
                                    
                                    if not line_found:
                                        rec.write({'order_line': [(0, False, value) for value in values]})
                            else:
                                for new_line in productos:
                                    line_found = False  # Reiniciar la bandera para cada elemento en productos
                                    for linea in rec.order_line:
                                        if linea.product_id.id == new_line['product_id'] and linea.price_unit == 0.01:
                                            line_found = True  # Establecer la bandera en True si se cumple la condición
                                            break  # Salir del bucle si se encuentra una línea que cumple la condición
                                    if not line_found:
                                        rec.write({'order_line': [(0, False, new_line)]})
                        elif pro.reward_type == 'discount':
                            pass
                            #revisar que es lo que se necesita para cumplir esta condicion
                #raise ValidationError(f'Promo automatica encontrada {pro.name} con los valores {values}')

    def _values_reward_product_id(self,program, veces_aplica=1):
        '''
        Metodo para crear la linea de partida nueva  
        '''
        taxes = program.reward_product_id.taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)
        taxes = self.fiscal_position_id.map_tax(taxes)
        value={
            'product_id': program.reward_product_id.id,
            'price_unit': 0.01,
            'product_uom_qty': program.reward_product_quantity * veces_aplica,
            'is_reward_line': True,
            'name': _("Free Product") + " - " + program.reward_product_id.name,
            'product_uom': program.reward_product_id.uom_id.id,
            'tax_id': [(4, tax.id, False) for tax in taxes],
        }
        return value

    def _values_reward_multi_product_id(self,program, veces_aplica=1):
        '''
        Metodo para crear lista de productos para las partidas
        '''
        taxes = program.reward_product_id.taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)
        taxes = self.fiscal_position_id.map_tax(taxes)
        values = []
        for linea in program.products_reward_line:
            values.append({
            'product_id': linea.product_id.id,
            'price_unit': 0.01,
            'product_uom_qty': linea.count_product * veces_aplica,
            'is_reward_line': True,
            'name': _("Free Product") + " - " + linea.product_id.name,
            'product_uom': linea.product_id.uom_id.id,
            'tax_id': [(4, tax.id, False) for tax in taxes],
            })
        return values
    
    def _remove_program_relation(self, programs):
        '''
        Metodo para eliminar todos los programas relacionados 
        '''
        for rec in self:
            programas_valdites=[]
            for pro in programs:
                if pro.promo_code_usage =='no_code_needed' and pro.promo_applicability == 'on_current_order':
                    programas_valdites.append(pro.id)
            for data in rec.no_code_promo_program_ids.ids:
                if data in programas_valdites:
                    pass
                else:
                    rec.env["sale.order"].browse(rec.id).write({'no_code_promo_program_ids':[(3,data,0)]})
    
    def ony_one_free_product_account_apply(self, pro, button=False):
        '''
        Metodo para devolver cuantes veces cabe un producto en la promocion  
        '''
        for rec in self:
            cantidad_aplicable = pro.rule_min_quantity
            compra_aplicable = pro.rule_minimum_amount
            cantidad_prodcuto = 0
            compra_min_aceptable = 0
            order_lines_x = (self.order_line - self._get_reward_lines()).filtered(lambda x: pro._get_valid_products(x.product_id))
            for x in order_lines_x:
                #print('#'*30, f'PRINTACOMEN producto aplicable {x.product_id.name}')
                cantidad_prodcuto += x.product_uom_qty
                compra_min_aceptable+= x.price_subtotal

            if compra_aplicable == 0:
                veces_aplica = cantidad_prodcuto // cantidad_aplicable
            else:
                if cantidad_prodcuto >= cantidad_aplicable:
                    veces_aplica = compra_min_aceptable // compra_aplicable
            return veces_aplica

    def reset_is_reward_line(self):
        '''
        Reseta la partida eliminado todos los productos agregador por reward y los registros de descuentos 
        '''
        for rec in self:
            for line in rec.order_line:
                if line.programas_ids != False:
                    line.discount = 0
                line.write({'programas_ids': [(5, 0, 0)]}) #? Eliminacacion de registos de progmas cumplen descuento en la linea 
                if line.is_reward_line == True:
                    rec.write({'order_line': [(3, line.id, 0)]}) #? Eliminacacion de linea creada Por producto

    @api.constrains('state')
    def verification_points(self):
        '''
        Verifica los puntos en la tabla actual activa para poder agregarlos
        '''
        for rec in self:
            #?Varibles de uso 
            puntos_acumulados =0 
            puntos = 0
            #? Validando cambio de estado 
            if rec.state == 'sale':
            #?Buscamos la tabla activa 
                if rec.points_use == False:
                    table_active = rec.env['loyalty.points'].sudo().search([('state','=','activo')])
                    #? Recorremos la partida 
                    for line in rec.order_line:
                        for table in table_active.points_lines_ids:
                            if line.product_id == table.product_id and line.is_reward_line != True:
                                puntos = 0
                                puntos = table.points * line.product_uom_qty
                                puntos_acumulados += puntos
                    rec.acomunlated_points = puntos_acumulados
                    rec.partner_id.acomulated_ponits += puntos_acumulados
                    rec.points_use = True
                else:
                    raise ValidationError(f'Los puntos de esta venta ya fueron agregados al cliente.')

    def write(self, values):
        '''
        Actualizacion de write para poder ver las promociones aplicadas en este pedido 
        '''
        res = super(NegblaSaleOrder, self).write(values)
        for rec in self:
            programs = rec._get_applicable_programs() 
            rec._remove_program_relation(programs)
        return res
    
    def discount_in_orden(self, pro):
        '''
        Aplica cuando el descuento sea sobre la orden completa
        aplicando el descuento en toda la orden
        [Resive como parametro programa de descuento]
        '''
        for rec in self:
            for line in rec.order_line:
                if line.is_reward_line != True:
                    if not pro.id in line.programas_ids.ids:
                        rec.no_code_promo_program_ids+=pro #agrega promocion
                        line.discount+= pro.discount_percentage
                        line.programas_ids+=pro
    def discount_in_cheap_product(self, pro):
        '''
        Aplica cuando el descuento sea sobre el producto mas barto
        [Resive como parametro programa de descuento]
        '''
        for rec in self:
            cheapest_line = None
            min_price = None
            for line in rec.order_line:
                if line.is_reward_line != True:
                    if min_price is None or line.price_unit < min_price:
                        min_price = line.price_unit
                        cheapest_line = line
            # se obtiene la linea mas barata y se agrega  
            if not pro.id in cheapest_line.programas_ids.ids:
                rec.no_code_promo_program_ids+=pro #agrega promocion
                cheapest_line.discount+= pro.discount_percentage
                cheapest_line.programas_ids+=pro


    def discount_in_selection_product(self, pro):
        '''
        Aplica cuando el descuento sea sobre productos espesificos  
        [Resive como parametro programa de descuento]
        '''
        for rec in self:
            for line in rec.order_line:
                if line.is_reward_line != True:
                    if line.product_id.id  in pro.discount_specific_product_ids.ids:
                        if not pro.id in line.programas_ids.ids:
                            rec.no_code_promo_program_ids+=pro #agrega promocion
                            line.discount+= pro.discount_percentage
                            line.programas_ids+=pro
