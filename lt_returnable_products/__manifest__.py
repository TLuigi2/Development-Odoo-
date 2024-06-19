
{
    'name': 'Productos retornables, envases y tarimas.',
    'version': '15.0',
    'depends': ['base','product','purchase','purchase_stock','stock_account','sale'],
    'license': 'GPL-3',
    'price': 84.6,
    'category' : 'purchase',
    'currency': 'USD',
    'summary': """Generacion de campos para relacion de productos retornables en productos principales, ticket de productos retornables y proceso de albaranes para agregar productos retornables de forma automatica, reporte productos retornables por partner.""",
    'description': "Control y trazabilidad para productos retornables.",
    'author': 'Negblasoft',
    'website': 'https://fixdoo.mx',
    'support': 'Fixdoo',
    'images': [],
#    'live_test_url': '',

    'data':[
        'security/ir.model.access.csv',
        'views/product_template_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_valuation_layer_view.xml',
        'views/ticket_returnable_products_view.xml',
        'wizard/returnable_report_wizard_view.xml'
     ],
     'assets': {
            'web.assets_backend': [
                'lt_returnable_products/static/src/js/action_manager.js',
            ],
    },
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
