# Copyright 2024 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Product Electrical Properties',
    'summary': """
        Add electrical properties in product and support for nextar-octopart api.""",
    'version': '18.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/product-attribute',
    'depends': [
        'product',
        'base',
        'mrp',
        'purchase',
        'product_manufacturer',
        'product_manufacturer_data',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/component_definition_properties.xml',
        'views/product_packaging_views.xml',
        'views/product_template_views.xml',
        # 'views/product_product_views.xml',
        'views/product_manufacturer.xml',
        'data/component_definition.xml',
    ],
    'demo': [
    ],
}
