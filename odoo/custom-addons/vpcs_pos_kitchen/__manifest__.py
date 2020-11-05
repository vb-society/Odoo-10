# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'POS Kitchen',
    'version': '10.0.0.2',
    'category': 'POS',
    'summary': 'POS Kitchen Bus Notification',
    'sequence': 0,
    'description': """
    POS Kitchen
    ===========
    This module provides pos kitchen screen functionality
    for manage the kitchen orders more efficient way.

    Features :-
    ===========
    More attractive and user friendly.
    Bus Notification Concept.
    Support modify order and apply new changes in kitchen screen after place order.
    Easily identify product based on category color.
    Sync product states.
    """,
    'author': 'VperfectCS',
    'maintainer': 'VperfectCS',
    'website': 'http://www.vperfectcs.com',
    'depends': ['pos_restaurant', 'web_widget_colorpicker'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/pos_views.xml',
        'views/pos_order_synch.xml',
    ],
    'qweb': [
        'static/src/xml/pos_redesign.xml',
    ],
    'support': 'info@vperfectcs.com',
    "license": "Other proprietary",
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 99,
    'currency': 'EUR',
}
