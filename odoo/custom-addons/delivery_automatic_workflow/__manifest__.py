# -*- coding: utf-8 -*-


{
    'name': 'Delivery Automatic Workflow',
    'version': '10.0.1.0.1',
    'category': 'Picking',
    'summary': 'Delivery Automatic: Delivery Automatic Implementation for Odoo version 10.0',
    'description': """Delivery Automatic""",
    'author': 'Virtual Business Society',
    'website': 'http://www.vb-society.com',
    'depends': ['sale_stock', 'website_sale', 'point_of_sale'],
    'data': [
        'views/sale_config_settings_views.xml',
        'views/pos_order_view.xml',
        'data/sale_config_settings_data.xml',
        'data/workflow.xml',
        # 'security/res_groups.xml',
        # 'security/ir.model.access.csv',
    ],
    'installable': True,
}
