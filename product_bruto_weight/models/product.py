# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = 'product.product'

    bruto_weight = fields.Float('Bruto Weight', digits=dp.get_precision('Stock Bruto Weight'),
        help="Bruto Weight of the product, packaging not included. The unit of measure can be changed in the general settings")
