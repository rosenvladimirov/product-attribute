# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name" : "Competitor info prices in sales",
    "version" : "12.0.1.0",
    "author" : "Rosen Vladimirov, dxFactory Ltd.",
    'category': 'Sales',
    "description": """
Add information for Competitor prices in sales and product. Allows to create priceslists based on Competitor info.
""",
    'depends': [
        'product',
        'base',
        'sale',
        'product_pricelist_extend',
    ],
    "demo" : [],
    "data" : [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'wizards/product_pricelist_print_view.xml',
    ],
    'license': 'AGPL-3',
    "installable": True,
}
