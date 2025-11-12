#  -*- coding: utf-8 -*-
#  Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class ProductCategory(models.Model):
    _inherit = "product.category"

    product_properties_ids = fields.One2many(
        comodel_name='product.properties.category.lines',
        inverse_name="product_categ_id",
        string='Category properties',
        ondelete='restrict'
    )
