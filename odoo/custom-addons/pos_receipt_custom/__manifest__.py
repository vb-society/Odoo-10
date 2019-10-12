# -*- coding: utf-8 -*-
# Copyright 2019 Reison Torres <https://www.vb-society.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    "name": """Customizable POS Receipt""",
    "summary": """Customize POS receipt""",
    "category": "Point of Sale",
    # "live_test_url": "",
    "images": ["images/pos_receipt_custom_main.png"],
    "version": "10.0.1.0.2",
    "application": False,

    "author": "Virtual Business Society, Reison Torres",
    "support": "info@vb-society.com",
    "website": "https://www.vb-society.com",
    "license": "LGPL-3",

    "depends": [
        "point_of_sale",
    ],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        "views/view.xml",
        "views/template.xml",
        "security/ir.model.access.csv",
        "data/data.xml",
    ],
    "demo": [
    ],
    "qweb": [
        "static/src/xml/pos.xml",
    ],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "uninstall_hook": None,

    "auto_install": False,
    "installable": True,
}
