# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.tools import float_is_zero
from odoo.tools import safe_eval
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit= "res.partner"

    discount_1 = fields.Integer(string="Descuento 1 %")
    discount_2 = fields.Integer(string="Descuento 2 %")
    discount_3 = fields.Integer(string="Descuento 3 %")
    discount_4 = fields.Monetary(string="Descuento 4 $")


    @api.depends('name')
    def name_get(self):
        '''
        Nuevo nombre al buscar un registro concatenando al inicio el id 
        '''
        result = []
        for partner in self:
            name = partner.name
            number = partner.id
            new_name = str(number) + ' - ' + name
            result.append((partner.id, new_name))
        return result
