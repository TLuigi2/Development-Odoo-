# -*- coding: utf-8 -*-
#Librerias generales de odoo 
from odoo import api, exceptions ,fields, models, _
from odoo.exceptions import UserError, ValidationError

#Nuevo modelo
class NegblaResParnter(models.Model):
    _inherit="res.partner"

    acomulated_ponits  = fields.Float(string="Puntos lealtad", copy=False, readonly=False)
    history_points_ids = fields.One2many('loyalty.historya.line','partner_id', copy=False, readonly=True)

    def edit_points(self):
        '''
        Wizard para la edicion de puntos lealtad cuando estos quieran ser utilizados        
        '''
        if self.acomulated_ponits == 0:
            raise ValidationError(f'Este cliente {self.name} no tiene puntos lealtad para usar, Puntos: {self.acomulated_ponits}')
        ctx = {
        'partner_id':self.id,
        }
        return {
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'res_model': 'wiz.loyalty.points',
        'views': [(False, 'form')],
        'view_id': False,
        'target': 'new',
        'context': ctx,
        }



class NegLoyaltyhistoryLine(models.Model):
    _name = "loyalty.historya.line"
    _description="Muestra historico de puntos restados"

    partner_id = fields.Many2one('res.partner',string="Contacto")
    points = fields.Integer(string="Puntos", readonly=True)
    motivo_de_resta = fields.Char(string="Motivo", readonly=True)


