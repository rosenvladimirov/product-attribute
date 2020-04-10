# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Datasheets Comments",
    'version': '11.0.1.0.0',
    'category': 'Accounting',
    "author": "Rosen Vladimirov <vladimirov.rosen@gmail.com>, "
              "dXFactory Ltd. <http://www.dxfactory.eu>",
    'website': 'https://github.com/rosenvladimirov/account-financial-tools',
    'license': 'AGPL-3',
    "depends": [
            'product_properties',
            'base_comment_template',
            'base',
            ],
    'data': [
            'views/ir_attachment_view.xml',
            ],
    'installable': True,
}
