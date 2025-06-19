# Copyright 2024 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Product Manufacturer Data',
    'summary': """Marafacturer data files for products""",
    'version': '18.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov,Odoo Community Association (OCA)',
    'website': 'https://github.com/rosenvladimirov/product-attribute',
    'depends': [
        'product',
        'product_brand',
        'product_manufacturer',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_manufacturer.xml',
        'views/product_template_views.xml',
        'views/product_supplierinfo_views.xml'
    ],
    'demo': [
    ],
}
