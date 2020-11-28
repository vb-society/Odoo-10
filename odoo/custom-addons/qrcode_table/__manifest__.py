# -*- coding: utf-8 -*-
#################################################################################
# Author      : Kanak Infosystems LLP. (<https://www.kanakinfosystems.com/>)
# Copyright(c): 2012-Present Kanak Infosystems LLP.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.kanakinfosystems.com/license>
#################################################################################

{
    "name": "POS Scan Table QR Code (Restaurant)",
    "version": "2.0",
    "category": "Point of Sale",
    "depends": ['website', 'point_of_sale', 'pos_product_modifiers', 'pos_restaurant'],
    'license': 'OPL-1',
    'website': 'https://www.kanakinfosystems.com',
    'author': 'Kanak Infosystems LLP.',
    'summary': 'QR code generated on table',
    "description": "Order from your table by scanning QR Code using your mobile.",
    "data": [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/assest.xml',
        'views/template.xml',
        'views/modal_templates.xml',
        'views/website_confirm_order_templates.xml',
        'views/pos_config_view.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'sequence': 1,
    "auto_install": False,
    "installable": True,
    "price": 150,
    "currency": "EUR",
}
