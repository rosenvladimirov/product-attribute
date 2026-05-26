# Copyright 2023-2025 Rosen Vladimirov, BioPrint Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Product Set Pricelist Fixed Price',
    'summary': 'Integration between product sets and fixed price pricelists',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, BioPrint Ltd., Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/product-attribute',
    'maintainers': ['rosenvladimirov'],
    'development_status': 'Beta',
    'depends': [
        'product_set',
        'product_pricelist_fixed_price',
    ],
    'data': [
        'views/product_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
