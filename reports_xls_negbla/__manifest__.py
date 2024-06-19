# -*- coding: utf-8 -*-

{
    'name': 'Reports XLS',
    'version': '15.0.1.0.0',
    "category": "Project",
    'author': 'Luigi Tolayo',
    'website': "https://negblasoft.com/",
    'maintainer': 'Negblasoft',
    'company': 'Negblasoft',
    'summary': """Habilita la opcion de poder generar un reporte xls""",
    'description': """El wizard o modelo deben de tener el metodo get_xlsx_report(self, data, response) """,
    'depends': ['base'],
    'license': 'AGPL-3',
    'data': [
            #'security/ir.model.access.csv',

            ],
    'assets': {
            'web.assets_backend': [
                'reports_xls_negbla/static/src/js/action_manager.js',
            ],
    },
    'images': [''],
    'installable': True,
    'auto_install': False,
}
