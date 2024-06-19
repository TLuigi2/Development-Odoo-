
{
    'name': 'Descuentos politicas comerciales proveedores compras',
    'version': '15.0',
    'depends': ['base','purchase','purchase_stock','stock_account'],
    'license': 'GPL-3',
    'price': 84.6,
    'category' : 'purchase',
    'currency': 'USD',
    'summary': """Generacion de campos para aplicacion de descuentos en proveedores, trazabilidad con modulo de compras para aplicar los descuentos parametrizados de forma automatica.""",
    'description': "Aplicacion de descuento sobre descuento en lineas de productos de ordenes de compra",
    'author': 'Luigi Tolayo',
    'website': 'https://negblasoft.com/',
    'support': 'tolayoluigi@gmail.com',
    'images': [],

    'data':[
        'security/ir.model.access.csv',
        'views/purchase_order_view.xml',
        'views/stock_picking_view.xml',
        'views/res_partner_view.xml',
     ],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
