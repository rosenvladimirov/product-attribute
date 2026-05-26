# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductBrand(models.Model):
    _inherit = 'product.brand'

    manufacturer_id = fields.Many2one('product.manufacturer', string="Product Manufacturer")
