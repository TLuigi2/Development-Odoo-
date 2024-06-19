
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class NegblaLoyaltePointWizard(models.TransientModel):
    _name = 'wiz.loyalty.points'
    _description = 'Ventana para la resta de puntos'

    partner_id = fields.Many2one('res.partner',string="Contacto")
    points = fields.Float(string="Puntos", required=True)
    motivo_de_resta = fields.Char(string="Motivo", required=True)

    def default_get(self, fields):
        '''
        Se obtiene los valores pasados por ctx 
        y se asignan los a los campos 
        '''
        res = super(NegblaLoyaltePointWizard, self).default_get(fields)
        partner_id = self._context.get('partner_id')
    
        res.update({'partner_id':partner_id})

        return res

    def user_point_partner(self):
        '''
        Resta los puntos lealtad y los agrega al historico 
        '''
        for rec in self:
            if rec.points <=0:
                raise ValidationError(f'NO pueden ser puntos menor o igual a 0 para restar')
            if rec.points > rec.partner_id.acomulated_ponits:
                raise ValidationError(f'No puedes restar mas puntos de los que tiene actualmente el cliente.')
            else:
                data={
                    'partner_id':rec.partner_id.id,
                    'points':rec.points,
                    'motivo_de_resta':rec.motivo_de_resta
                }
                rec.env['loyalty.historya.line'].create(data)
                rec.partner_id.acomulated_ponits -= rec.points
