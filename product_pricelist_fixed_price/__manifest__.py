# Copyright 2023 Rosen Vladimirov, BioPrint Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Product Price List Fixed Price',
    'summary': 'Add view to fill price directly in product forms',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, BioPrint Ltd., Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/product-attribute',
    'maintainers': ['rosenvladimirov'],
    'development_status': 'Beta',
    'depends': [
        'product',
        'sale',
    ],
    'data': [
        'views/product_category_views.xml',
        'views/product_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
