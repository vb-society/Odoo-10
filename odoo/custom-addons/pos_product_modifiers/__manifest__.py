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
    'name': "POS Product Modifiers",
    'version': '1.0',
    'summary': 'POS Product Modifiers',
    'description': """
POS Product Modifiers
=====================
    """,
    'license': 'OPL-1',
    'author': "Kanak Infosystems LLP.",
    'website': "https://www.kanakinfosystems.com",
    'category': "POS",
    'depends': ['point_of_sale'],
    'images': [
        'static/description/banner.png',
    ],
    'data': [
        'views/modifires_view.xml',
        'security/ir.model.access.csv'
    ],
    'sequence': 1,
    'application': True,
}
