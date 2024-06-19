# -*- coding: utf-8 -*-
#Librerias generales de odoo 
from odoo import api, exceptions ,fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class NegLoyaltyPoints(models.Model):
    _name = "loyalty.points"
    _description="Puntos lealtad Negbla"
    _inherit = ['mail.thread','mail.activity.mixin']

    name =  fields.Char(string="Nombre de lista de puntos", copy=False, required=True)
    state = fields.Selection([('activo', 'Activo'),('inactivo','Inactivo')], string="Estado", copy=False, default='inactivo')
    points_lines_ids = fields.One2many('loyalty.points.line', 'loyalty_id', string="Lineas de puntos")

    @api.constrains('state')
    def unique_table_points_active(self):
        '''
        Valida que solo exista programa leatad activo 
        '''
        for rec in self:
            validation_unique  =   rec.env['loyalty.points'].search([('state','=', 'activo')])
            if len(validation_unique)>1:
                raise ValidationError(f'No puede existir mas de una tabla lealtad activa.')
    
    @api.constrains('points_lines_ids')
    def verifica_producto(self):
        '''
        Verifica que un producto no se agrege dos ces 
        '''
        for rec in self:
            for line in rec.points_lines_ids:
                search_product = rec.env['loyalty.points.line'].sudo().search([('product_id','=',line.product_id.id),('loyalty_id','=',rec.id)])
                if len(search_product)>1:
                    raise ValidationError(f'No puede registrarse el mismo producto mas de una vez.')
    

class NegLoyaltyPointsLine(models.Model):
    _name = "loyalty.points.line"
    _description="Lineas de partida leatad"
    product_id = fields.Many2one('product.product',string='producto', required=True)
    points = fields.Float(string="Puntos", required=True)
    loyalty_id = fields.Many2one('loyalty.points',string='Programa lealtad')

    @api.constrains('points')
    def no_zero_points(self):
        '''
        Comprueba de no agregen a la tabla puntuaje menor a cer0
        '''
        for rec in self:
            if rec.points < 0:
                raise ValidationError(f'No puedes agregar puntos menor a cero')




