# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Customs taric codes',
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': 'Base module for Customs taric codes',
    'author': 'Rosen Vladimirov, dXFactory Ltd.',
    'website': 'https://github.com/rosenvladimirov/product-attribute',
    'depends': [
        'base',
        'account',
        'product_harmonized_system'
    ],
    'data': [
        'views/account_invoice_view.xml',
        'views/account_view.xml',
        'views/hs_code.xml',
        'views/res_partner_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
}
