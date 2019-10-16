# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Product properties',
    'version': '12.0.1.0.0',
    'category': 'Product',
    'sequence': 5,
    'summary': 'Product properties',
    'description': """
This module serves to provide a parallel information base for basic product features; this information does not affect variants but is linked to tach
 Added the ability to organize documentation related to the manufacturer and product. 
This module can be used in the food industry to describe allergen-related ingredients as well as supporting documents.
""",
    'author': 'Rosen Vladimirov, dXFactory Ltd.',
    'depends': [
                'product',
                'stock',
                'purchase',
                'web_widget_image_url',
                'product_brand',
                ],
    'data': [
            'security/product_properties.xml',
            'security/ir.model.access.csv',
            'views/ir_attachment_view.xml',
            'views/product_properties_views.xml',
            'views/product_views.xml',
            'views/purchase_views.xml',
            'views/product_brand_view.xml',
            'views/res_partner_view.xml',
            ],
    'demo': [],
    'installable': True,
}
