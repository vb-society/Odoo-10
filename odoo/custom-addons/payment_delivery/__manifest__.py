# -*- coding: utf-8 -*-

{
    'name': 'Delivery Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: On Delivery Implementation for Odoo version 10.0',
    'version': '1.0',
    'description': """Delivery Payment Acquirer""",
    'author': 'Virtual Business Society',
    'website': 'http://www.vb-society.com',
    'depends': ['website_portal_sale'],
    'data': [
        'views/payment_delivery_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'auto_install': True,
}
