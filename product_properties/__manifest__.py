# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Product properties',
    'version': '11.0.2.0.9',
    'category': 'Product',
    'sequence': 5,
    'summary': 'Product properties',
    'description': """
Informations about Product properties
=====================================
T

T
""",
    'author': 'Rosen Vladimirov, dXFactory Ltd.',
    'depends': [
                'base',
                'product',
                'stock',
                'purchase',
                'web_widget_image_url',
                'product_brand',
                'l10n_bg_extend',
                ],
    'data': [
            'security/product_properties.xml',
            'security/ir.model.access.csv',
            'views/assets.xml',
            'views/ir_attachment_view.xml',
            'views/product_properties_views.xml',
            'views/product_views.xml',
            'views/purchase_views.xml',
            'views/product_brand_view.xml',
            'views/res_partner_view.xml',
            'views/sale_views.xml',
            'views/account_invoice_view.xml',
            'views/stock_picking_views.xml',
            'views/product_properties_linename_templates.xml',
            'views/report_product_properties.xml',
            'views/report_sale_templates.xml',
            'views/report_purchase_order_templates.xml',
            'views/report_invoice.xml',
            'views/report_accepted_delivery.xml',
            ],
    'demo': [],
    'installable': True,
}
