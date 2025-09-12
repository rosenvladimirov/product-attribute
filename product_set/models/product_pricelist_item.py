#  Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    product_set_id = fields.Many2one('product.set', 'Product Set')
    product_set_line_id = fields.Many2one('product.set.line', 'Product Set Line')
