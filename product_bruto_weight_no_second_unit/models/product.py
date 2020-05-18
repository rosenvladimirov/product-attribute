# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = 'product.product'

    bruto_weight = fields.Float('Brut Weight', digits=dp.get_precision('Stock Weight'),
        help="Bruto Weight of the product, packaging not included. The unit of measure can be changed in the general settings")
    product_tray = fields.Integer('Consumable products/tray')
    per_layrs = fields.Integer('Trays per layer')
    europallet_lears = fields.Integer('Layers per europallet')
    box_barcode = fields.Char("Box EAN14")

