# -*- coding: utf-8 -*-
# dXFactory Proprietary License (dXF-PL) v1.0. See LICENSE file for full copyright and licensing details.
{
    'name': 'Product prefix label',
    'version': '1.0',
    'category': 'Manufacturing',
    'sequence': 2,
    'summary': 'Add product labels prefix',
    'description': """
Product label prefix
====================
T

T
""",
    'author': 'dXFactory ltd.',
    'website': 'https://www.dxfactory.eu',
    'depends': ['product', 'stock'],
    'data': [
            'security/ir.model.access.csv',
            'views/product_views.xml',
            'views/product_template.xml',
            'views/sale_report_templates.xml',
            'views/report_invoice.xml',
            'views/stock_production_lot_views.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
