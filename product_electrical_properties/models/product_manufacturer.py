# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ProductManufacturer(models.Model):
    _inherit = "product.manufacturer"

    reelpackaging_ids = fields.One2many(
        'product.packaging.reel',
        'manufacturer_id',
        string='Standard Product Packages',
    )
