# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Product technical properties',
    'version': '1.0',
    'category': 'Product',
    'sequence': 5,
    'summary': 'Product technical properties',
    'description': """
Informations about Product technical properties
================================================
T

T
""",
    'author': 'Rosen Vladimirov',
    'depends': [
                'product',
                'stock',
                'purchase',
                'web_tree_image'
                ],
    'data': [
            'security/product_technical_properties.xml',
            'security/ir.model.access.csv',
            'views/product_properties_views.xml',
            'views/stock_production_lot_views.xml',
            'views/menus.xml'
            ],
    'demo': [],
    'installable': True,
}
