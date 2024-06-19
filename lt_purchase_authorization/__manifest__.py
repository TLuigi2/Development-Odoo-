
{
    'name': 'Autorizacion de Compras.',
    'version': '15.0',
    'depends': ['base','purchase_requisition','hr','purchase_stock'],
    'license': 'GPL-3',
    'price': 84.6,
    'category' : 'purchase',
    'currency': 'USD',
    'summary': """Generación de campos para la Autorizacion de Ordenes de Compras directas e indirectas.""",
    'description': "Aplicacion de validaciones sobre Ordenes de Compra directas e indirectas.",
    'author': 'Luigi Tolayo',
    'website': 'https://negblasoft.com/',
    'support': 'tolayoluigi@gmail.com',
    'images': [],
#    'live_test_url': '',

    'data':[
        'security/lt_groups.xml',
        'security/ir.model.access.csv',
        'data/cat_states_purchase.xml',
        'views/res_config_settings_view.xml',
        'views/purchase_requisition_view.xml',
        'views/purchase_order_view.xml' 
     ],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
