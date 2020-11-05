# -*- coding: utf-8 -*-
# Part of AktivSoftware See LICENSE file for full copyright
# and licensing details.
{
    "name": "Restaurant Customization",
    "category": "Point Of Sale",
    'summary': 'Manage Kitchen screen and Order screen',
    'website': 'http://www.aktivsoftware.com',
    'author': 'Aktiv Software',
    'license': "OPL-1",
    'price': 49.00,
    'currency': "EUR",
    'version': '10.0.1.0.0',
    'description': """
        Using this module user can track pos orders into kitchen easily.
    """,
    "depends": [
        'base', 'pos_discount', 'website',
        'point_of_sale', 'pos_restaurant',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/discount_type_data.xml',
        'data/pos_category_data.xml',
        'data/pos_restaurant_data.xml',
        'data/res_users_data.xml',
        'view/pos_order.xml',
        'view/pos_category_discount_view.xml',
        'view/pos_config_view.xml',
        'view/res_users_views.xml',
        'view/pos_category_views.xml',
        'views/pos_order_templates.xml',
        'views/order_screen_template.xml',
        'views/kitchen_screen_template.xml',
    ],
    "qweb": [
        'static/src/xml/pos.xml',
        'static/src/xml/pos_order_type.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'auto_install': False,
    'installable': True,
    'application': False,
}
