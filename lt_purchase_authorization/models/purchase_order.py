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

    _inherit = 'purchase.order'

    def _get_state_indirecta_id(self):
        return self.env['states.purchase'].search([('name','=','Presupuesto')]).id
    
    def _get_state_indirecta_name(self):
        return self.env['states.purchase'].search([('name','=','Presupuesto')]).name

    department = fields.Many2one('hr.department',string="Departamento", copy=False)
    type_purchase = fields.Selection(selection=[('Directa','Directa'),('Indirecta','Indirecta')], string="Tipo Compra", default="Indirecta")    
    state_pur_indirecta = fields.Many2one('states.purchase', string="Estados", default=_get_state_indirecta_id, copy=False)
    state_pur_indirecta_name = fields.Char(string="Estado Name", default=_get_state_indirecta_name, copy=False)
    check_indirecta = fields.Boolean(string="Pasa del Monto", copy=False)
    check_directa = fields.Boolean(string="Pasa del Monto", copy=False)
    state_name = fields.Selection(selection=[
        ('draft','Solicitud de cotización'),
        ('sent','Solicitud de cotización enviada'),
        ('to approve','Para aprobar'),
        ('purchase','Orden de compra'),
        ('done','Bloqueado'),
        ('cancel','Cancelado'),
        ('Presupuesto','Presupuesto'),
        ('Apro GTE','Apro GTE'),
        ('Apro FIN','Apro FIN'),
        ('Bloqueado','Bloqueado')], string="Estado", default="draft", copy=False, index=True, tracking=3,)

    '''
        Funcion que valida si el total es mayor al establecido para las compras Indirectas
    '''
    @api.onchange('order_line')
    def _onchange_order_line(self):
        valor = float(self.env['ir.config_parameter'].sudo().get_param('aprob_pur_ind'))
        valor_minimo = float(self.env['ir.config_parameter'].sudo().get_param('po_double_validation_amount'))
        if self.amount_total > valor:
            self.check_indirecta = True
        else:
            self.check_indirecta = False
        if self.amount_total > valor_minimo:
            self.check_directa = True
        else:
            self.check_directa = False

    '''
        Funcion que actualiza los campos del purchase.requisition en purchase.order
    '''
    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        if not self.requisition_id:
            return

        self = self.with_company(self.company_id)
        requisition = self.requisition_id
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = requisition.vendor_id
        payment_term = partner.property_supplier_payment_term_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.with_company(self.company_id).get_fiscal_position(partner.id)

        self.department = self.requisition_id.department
        self.type_purchase = self.requisition_id.type_purchase
        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id,
        self.company_id = requisition.company_id.id
        self.currency_id = requisition.currency_id.id
        if not self.origin or requisition.name not in self.origin.split(', '):
            if self.origin:
                if requisition.name:
                    self.origin = self.origin + ', ' + requisition.name
            else:
                self.origin = requisition.name
        self.notes = requisition.description
        self.date_order = fields.Datetime.now()

        if requisition.type_id.line_copy != 'copy':
            return

        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            # Compute name
            product_lang = line.product_id.with_context(
                lang=partner.lang or self.env.user.lang,
                partner_id=partner.id
            )
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            # Compute taxes
            taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id)).ids

            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_po_id:
                product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
            else:
                product_qty = line.product_qty
                price_unit = line.price_unit

            if requisition.type_id.quantity_copy != 'copy':
                product_qty = 0

            # Create PO line
            order_line_values = line._prepare_purchase_order_line(
                name=name, product_qty=product_qty, price_unit=price_unit,
                taxes_ids=taxes_ids)
            order_lines.append((0, 0, order_line_values))
        self.order_line = order_lines

    
    '''
        Funcion en botones para cambio de estatus
    '''

    def change_quote_aprogte(self):
        self.state_pur_indirecta = self.env['states.purchase'].search([('name','=','Apro GTE')]).id
        self.state_pur_indirecta_name = self.env['states.purchase'].search([('name','=','Apro GTE')]).name
        self.state_name = self.env['states.purchase'].search([('name','=','Apro GTE')]).name
    
    def change_aprogte_aprofin(self):
        self.check_indirecta = False
        self.state_pur_indirecta = self.env['states.purchase'].search([('name','=','Apro FIN')]).id
        self.state_pur_indirecta_name = self.env['states.purchase'].search([('name','=','Apro FIN')]).name
        self.state_name = self.env['states.purchase'].search([('name','=','Apro FIN')]).name
    
    def change_aprodir_bloq(self):
        self.button_confirm()

    def button_approve(self, force=False):
        if self.type_purchase == 'Indirecta':
            self.write({
                    'state_pur_indirecta':self.env['states.purchase'].search([('name','=','Bloqueado')]).id,
                    'state_pur_indirecta_name':self.env['states.purchase'].search([('name','=','Bloqueado')]).name,
                    'state_name':self.env['states.purchase'].search([('name','=','Bloqueado')]).name
                    })
        self.write({'state': 'purchase', 'state_name':'purchase', 'date_approve': fields.Datetime.now()})
        self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
        self._create_picking()
        return {}

    def button_confirm_approve(self):
        for order in self:
            order.state = 'to approve' 
    
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            order.button_approve()
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True
    
    def button_draft(self):
        if self.type_purchase == 'Indirecta':
            self.write({'state': 'draft','state_name':'Presupuesto','state_pur_indirecta_name':'Presupuesto','state_pur_indirecta':self.env['states.purchase'].search([('name','=','Presupuesto')]).id})
        else:
            self.write({'state': 'draft','state_name':'draft'})
        return {}

    def button_cancel(self):
        for order in self:
            for inv in order.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise UserError(_("Unable to cancel this purchase order. You must first cancel the related vendor bills."))

        self.write({'state': 'cancel','state_name':'cancel'})

    def button_unlock(self):
        self.write({'state': 'purchase','state_name':'purchase'})

    def button_done(self):
        self.write({'state': 'done','state_name':'done'})
    
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_rfq_as_sent'):
            self.filtered(lambda o: o.state == 'draft').write({'state': 'sent','state_name':'sent'})
        return super(PurchaseOrder, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

    def print_quotation(self):
        self.write({'state': "sent",'state_name':"sent"})
        return self.env.ref('purchase.report_purchase_quotation').report_action(self)

        
    