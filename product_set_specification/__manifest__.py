# Copyright 2025 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Product Set Specifications',
    'version': '18.0.1.0.0',
    'category': 'Sales/Product',
    'summary': 'Add product set specifications on product sets',
    'author': 'Rosen Vladimirov, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/product-attribute',
    'license': 'AGPL-3',
    'description': """
Product Set Specifications
==========================
This module extends the product_set module to add specifications functionality
to product sets, similar to the product_specifications module.
    """,
    'depends': [
        'product_set',
        'product_specifications',
    ],
    'data': [
        'views/product_set_views.xml',
    ],
    'demo': [],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'assets': {},
}
