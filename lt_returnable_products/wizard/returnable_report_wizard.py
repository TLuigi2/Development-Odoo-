# -*- coding: utf-8 -*-

from datetime import datetime
import json
import datetime
import pytz
import io
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class NegblaReportReturnable(models.TransientModel):
    _name = 'wizard.returnable.report'

    partner_select = fields.Many2one('res.partner', string='Proveedor')

    def print_valuation_report_xls(self):
        print("Ingresa en accion print_valuation_report_xls")
        record = self.env['res.partner'].browse(1)
        data = {
            'ids': self.ids,
            'model': self._name,
            'record': record.id,
            'tipo':'layout'
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'wizard.returnable.report',
                     'options': json.dumps(data,default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Reporte de retornables',
                     },
            'report_type': 'xlsx_lt'
        }

    def get_xlsx_report(self,data,response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        user_obj = self.env.user
        wizard_record = request.env['wizard.returnable.report'].search([])[-1]
        format1 = workbook.add_format({'font_size': 22, 'bg_color': '#D3D3D3','align':'center'})
        format2 = workbook.add_format({'font_size': 12 })
        format3 = workbook.add_format({'font_size': 11,'bg_color': '#E0AB31'})
        format4 = workbook.add_format({'font_size': 11, 'bg_color': '#E4ED54'})
        format5 = workbook.add_format({'font_size': 11, 'bg_color': '#64ADE9'})
        format6 = workbook.add_format({'font_size': 12, 'bold': True})
        sheet = workbook.add_worksheet("Inventario retornables general")
        registros_por_proveedor = self.env['stock.valuation.layer'].search([('product_id.type', '=', 'product'),('product_id.returnable', '=', True)])
            
        sheet.write(0, 0, 'Referencia',format6)
        sheet.write(0, 1, 'Producto',format6)   
        sheet.write(0, 2, 'Proveedor',format6)
        sheet.write(0, 3, 'Cantidad',format6)
        sheet.write(0, 4, 'Unidad de medida',format6)
        
        sheet.set_column(0, 0, 25)
        sheet.set_column(0, 1, 15)
        sheet.set_column(0, 2, 15)
        sheet.set_column(0, 3, 15)
        sheet.set_column(0, 4, 15)
        row_p = 1
        
        # Diccionario para almacenar los totales agrupados
        registros_agrupados = {}

        # Iterar sobre los registros y realizar la sumatoria del campo quantity
        for registro in registros_por_proveedor:
            proveedor = registro.partner_id
            producto = registro.product_id
            cantidad = registro.quantity
            origen = registro.stock_move_id.origin or ""

            # Generar una clave única para agrupar por proveedor y producto
            clave = (proveedor, producto)

            # Verificar si la clave ya existe en el diccionario
            if clave in registros_agrupados:
                # Si la clave existe, agregar la cantidad al valor existente
                registros_agrupados[clave][0] += cantidad
                registros_agrupados[clave][1].append(origen)
            else:
                # Si la clave no existe, crear un nuevo registro con la cantidad y el origen
                registros_agrupados[clave] = [cantidad, [origen]]

        # Recorrer los registros agrupados y obtener los valores
        for clave, datos in registros_agrupados.items():
            proveedor, producto = clave
            cantidad_total = datos[0]
            origen_concatenado = ",".join(datos[1])
            if producto.default_code == False:
                default_code = ""
            else:
                default_code = producto.default_code 
            # Realizar las operaciones que necesites con los valores agrupados
            sheet.write(row_p, 0, default_code,format2)
            sheet.write(row_p, 1, producto.name,format2)
            sheet.write(row_p, 2, proveedor.name,format2)
            sheet.write(row_p, 3, cantidad_total,format2)
            sheet.write(row_p, 4, producto.uom_id.name,format2)
            row_p += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())

        output.close()

