# -*- coding: utf-8 -*-
# Part of AktivSoftware See LICENSE file for full copyright
# and licensing details.
{
    "name": "Restaurant Customization Extend",
    "category": "Point Of Sale",
    'summary': 'Manage Kitchen screen and Order screen',
    'website': 'http://www.vb-society.com',
    'author': 'Reison Torres',
    'license': "OPL-1",
    'version': '10.0.1.0.0',
    'description': """
        Using this module user can track pos orders into kitchen easily.
    """,
    "depends": [
        'bus', 'restaurant_customization',
    ],
    'data': [
        'views/pos_order_templates.xml',
        'views/order_screen_template.xml',
        'views/kitchen_screen_template.xml',
    ],
    "qweb": [
        'static/src/xml/pos_order_type.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'auto_install': False,
    'installable': True,
    'application': False,
}
