# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name" : "Add GS1, UDI and hibc standarts",
    "version" : "12.0.1.0",
    "author" : "Rosen Vladimirov, dXFactory Ltd.",
    'category': 'hidden',
    "description": """
Add support for GS1 [GTIN+AI(n)], UDI and HIBC standarts in barcode nomenclature
    """,
    'depends': [
        'stock',
        'product_expiry',
    ],
    "demo" : [],
    "data" : [
        'views/production_lot_views.xml',
        'views/barcodes_view.xml',
    ],
    'license': 'AGPL-3',
    "installable": True,
}
