# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = 'product.product'

    alt_name = fields.Char('Alternative names', translate=True,
                           help="Please fill the alternative name for this product variant")
