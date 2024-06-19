from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
import ast

class NegblaCouponProgram(models.Model):
    _inherit = "coupon.program"

    products_reward_line = fields.One2many('negproducts.reward','coupon_program_id',string="Productos de promocion")
    multi_free_prductos = fields.Boolean(string="Multiples productos gratis")
    programs_count  = fields.Integer(string="aplicados", compute="_count_programs")

    @api.constrains('multi_free_prductos')
    def validation_muiti_products_free(self):
        '''
        Metodo que valida si existen productos registros para muilti productos
        '''
        for rec in self:
            if rec.multi_free_prductos == True: 
                sarch_lines = rec.env['negproducts.reward'].sudo().search([('coupon_program_id','=',rec.id)])
                if len(sarch_lines) == 0:
                    raise ValidationError(f'No puede activar multiples productos gratis y dejar vacia la lista de productos gratis.')

    def _count_programs(self):
        '''
        Cuenta cuantos ventas estan relacionados al programa
        '''
        for record in self:
            contador = self.env["sale.order"].search([('no_code_promo_program_ids','in', [record.id])])
            record.programs_count = len(contador)
            #raise exceptions.ValidationError(f'Esto es contador {record.server_count}')

    def sales_in_progromas(self):
        '''
        Muesta las vistas tree,from de ventas
        que esten relacionadas al progroma.
        '''
        return{
            "type":"ir.actions.act_window",
            "name":"ventas con el progroma " +self.name,
            "res_model":"sale.order",
            "views":[[False,"tree"],[False,"form"]], #acceso a la vista por listas  [false, "type_view"]
            "target":"self", #self para misma ventan new para nueva ventana
            "domain":[["no_code_promo_program_ids","in",self.id]]
        }

    @api.onchange('active','state_coupon_progrm')
    def control_active_program_sale_coupon(self):
        '''
        Aciva o desactiva el programa  
        '''
        for rec in self:
            if rec.state_coupon_progrm == 'inactive':
                rec.active == False
            elif rec.state_coupon_progrm == 'active':
                rec.active == True


    def _get_valid_products(self, products):
        """Get valid products for the program.

        :param products: records of product.product
        :return: valid products recordset
        """
        if self.rule_products_domain and self.rule_products_domain != "[]":
            domain = ast.literal_eval(self.rule_products_domain)
            return products.filtered_domain(domain)
        return products
    





class NegblaProductsFree(models.Model):
    _name = "negproducts.reward"
    _description="Lineas de partida de multiples productos gratis"

    coupon_program_id = fields.Many2one('coupon.program',string='Programa Promociones')
    product_id = fields.Many2one('product.product',string='producto', required=True)
    count_product = fields.Integer(string="Cantidad", required=True, default=1)

    @api.constrains('count_product','product_id')
    def no_zero_or_mim(self):
        '''
        Valida que no exista cantidad menor a cero o cero 
        '''
        for rec in self:
            if rec.count_product == 0 or rec.count_product < 0:
                raise UserError(f'La cantidad para un producto gratis no puede ser cero o menor a cero en Productos Gratis')





