# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Product properties',
    'version': '18.0.1.0.0',
    'category': 'Product',
    'sequence': 5,
    'summary': 'Product properties',
    "license": "AGPL-3",
    "website": "https://github.com/OCA/product-attribute",
    'description': """
Information's about Product properties
""",
    'author': 'Rosen Vladimirov, '
              'BioPrint Ltd.',
    'depends': [
        'sale',
        'base',
        'product',
        'stock',
        'purchase',
        'product_manufacturer',
        'product_brand',
        'l10n_bg_report_stock',
        'l10n_bg_report_theme',
        'documents',
        'documents_product',
        'queue_job'
    ],
    'data': [
        'security/product_properties.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_set_all_print_properties.xml',
        'wizard/wizard_set_category_product_properties.xml',
        'views/product_properties_views.xml',
        'views/product_properties_static_view.xml',
        'views/product_properties_type_view.xml',
        'views/product_properties_category_view.xml',
        'views/product_properties_print_view.xml',
        'views/product_properties_print_category_view.xml',
        'views/product_template_views.xml',
        'views/product_views.xml',
        'views/purchase_views.xml',
        'views/res_partner_view.xml',
        'views/sale_order_views.xml',
        'views/account_move_view.xml',
        'views/stock_picking_views.xml',
        'views/product_properties_linename_templates.xml',
        'views/report_product_properties.xml',
        'views/report_sale_templates.xml',
        'views/report_purchase_order_templates.xml',
        'views/report_deliveryslip.xml',
        'views/report_invoice.xml',
        'views/report_templates.xml',
        'views/report_accepted_delivery_document.xml',
        'views/menus.xml',
    ],
    'demo': [],
    'installable': True,
    'assets': {
        'web.report_assets_common': [
            'product_properties/static/src/layout_product_properties.scss'
        ],
        'web.assets_backend': [
            'product_properties/static/src/layout_product_properties.scss',
        ]
    }
}
