# -*- coding: utf-8 -*-

{
    'name': 'PayU Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: PayU Latam Implementation for Odoo version 10.0',
    'version': '10.0',
    'description': """PayU Latam Payment Acquirer""",
    'author': 'Virtual Business Society',
    'website': 'http://www.vb-society.com',
    'depends': ['payment'],
    'data': [
        'views/payment_payulatam_template.xml',
        'views/payment_acquirer.xml',
        'views/res_config_view.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}
