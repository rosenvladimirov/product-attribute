{
    'name': 'Product Specifications',
    'category': 'Sales/Inventory',
    'author': "Rosen Vladimirov, dXFactory Ltd.",
    'summary': 'Add product specifications on products and product variants',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'description': """
Product Specifications
=====================
This module allows adding detailed specifications to products and product variants.
    """,
    'depends': ['product', 'stock', 'account','sale'],
    'data': [
        'views/product_template_views.xml',
        'views/product_views.xml',
        'views/menus.xml',
        'views/report_invoice.xml',
        'views/report_sale_templates.xml'
    ],
    'demo': [],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'assets': {},
}
