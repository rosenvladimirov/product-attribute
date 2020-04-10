# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.api import Environment, SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = Environment(cr, SUPERUSER_ID, {})
    for product in env['product.template'].search([('manufacturer', '!=', False)]):
        manufacturer = env['product.manufacturer'].search([('manufacturer', '=', product.manufacturer.id), ('product_tmpl_id', '=', product.id)])
        if not manufacturer:
            env['product.manufacturer'].create({'product_tmpl_id': product.id, 'manufacturer': product.manufacturer.id, 'manufacturer_pref': product.manufacturer_pref, 'manufacturer_purl': product.manufacturer_purl})
