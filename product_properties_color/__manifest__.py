# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Product properties color scheme',
    'version': '11.0.1.0.0',
    'category': 'Product',
    'sequence': 5,
    'summary': 'Product properties color scheme',
    'description': """
Informations about Product properties
=====================================
T

T
""",
    'author': 'Rosen Vladimirov, '
              'BioPrint Ltd.',
    'depends': [
                'sale_product_set',
                'product_properties',
                'web_tree_dynamic_colored_field',
                ],
    'data': [
            'wizard/wizard_set_all_print_properties.xml',
            'views/product_properties_views.xml',
            'views/account_invoice_view.xml',
            'views/sale_views.xml',
            'views/stock_picking_views.xml',
            'security/ir.model.access.csv',
            ],
    'demo': [],
    'installable': True,
    'license': 'Other proprietary',
}
