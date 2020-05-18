# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductSecondaryUnit(models.Model):
    _inherit = 'product.secondary.unit'

    packaging_ids = fields.One2many(
        'product.packaging', 'product_tmpl_id', 'Product Packages',
        help="Gives the different ways to package the same product.")
