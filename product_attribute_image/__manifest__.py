# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Product Attribute Image',
    'version': '11.0.1.0.0',
    'category': 'Product',
    'summary': "Product Attribute Image",
    'author': 'Rosen Vladimirov',
    'license': 'AGPL-3',
    'depends': [
        'product',
        'website_sale',
        'web_tree_image'
        ],
    'data': [
        'views/product_attribute_views.xml',
        'views/template.xml'
    ],
    'installable': True,
    'auto_install': False
}
