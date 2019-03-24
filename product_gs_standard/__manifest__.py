# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name" : "Add GS1, UDI and hibc standarts",
    "version" : "11.0.1.0",
    "author" : "Rosen Vladimirov",
    'category': 'hidden',
    "description": """
Add support for GS1 [GTIN+AI(n)], UDI and HIBC standarts in barcode nomenclature
    """,
    'depends': [
        'stock',
    ],
    "demo" : [],
    "data" : [
        'views/production_lot_views.xml',
    ],
    'license': 'AGPL-3',
    "installable": True,
}
