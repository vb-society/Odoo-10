# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name" : "POS Multi Session Sync",
    "version" : "10.0.0.1",
    "category" : "Point of Sale",
    "depends" : ['base','bus','sale','point_of_sale'],
    "author": "BrowseInfo",
    'summary': 'This apps allows POS Multi Session Management.',
    "description": """
    
    Purpose :- 
This apps allows POS Multi Session Management.
    POS Multi Session Management
    pos session synch
    pos order synch
    pos multi session synch
    pos Synchronization

    POS Multi Session Synchronization
    pos session Synchronization
    pos order Synchronization
    pos multi session Synchronization
    """,
    "website" : "www.browseinfo.in",
    "data": [
        'security/ir.model.access.csv',
        'views/custom_pos_view.xml',
        'views/pos_multi_session.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'live_test_url':'https://www.youtube.com/watch?v=Kc5WKf4-qO4&feature=em-uploademail',
    "auto_install": False,
    "installable": True,
    "images":['static/description/Banner.png'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
