# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Product Distrubutor',
    'version': '11.0.1.0.0',
    'summary': 'Adds distributor in supplier info.',
    'author': 'dXFactory',
    'license': 'AGPL-3',
    'category': 'Product',
    'depends': ['product', 'base', 'l10n_bg_extend'],
    'data': [
        'views/product_distributor_view.xml',
        'views/res_partner_view.xml',
    ],
    'auto_install': False,
    'installable': True,
}
