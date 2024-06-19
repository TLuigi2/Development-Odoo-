# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    aprob_pur_ind = fields.Monetary(string="Aprobación por Dirección Compras Indirectas")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        aprob_pur_ind = params.get_param('aprob_pur_ind', default=False)
        res.update(aprob_pur_ind=float(aprob_pur_ind))
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("aprob_pur_ind",
        self.aprob_pur_ind)