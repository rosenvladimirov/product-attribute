# Copyright 2023-2025 Rosen Vladimirov, BioPrint Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Product Properties Product Set',
    'summary': 'Add support for product properties in product sets',
    'version': '18.0.1.0.0',
    'category': 'Product/Management',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, BioPrint Ltd., Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/product-attribute',
    'maintainers': ['rosenvladimirov'],
    'development_status': 'Beta',
    'depends': [
        'product_set',
        'product_properties',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_set.xml',
        'views/product_properties_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_views.xml',
        'views/account_move_view.xml',
        'views/stock_picking_views.xml',
        'wizard/wizard_set_category_product_properties.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
