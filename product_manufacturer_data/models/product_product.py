# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    manufacturer_ids = fields.One2many(
        'product.manufacturer',
        'product_id',
        'Manufacturers'
    )
