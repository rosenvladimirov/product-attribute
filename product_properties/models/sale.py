# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    use_product_description = fields.Boolean(default=True)
    print_properties = fields.One2many('product.properties.print.sale', 'order_id', 'Print poperties')


class ProductProperties(models.Model):
    _name = "product.properties.print.sale"
    _description = "Product properties for printing in sale"

    name = fields.Many2one("product.properties.type", string="Property name", required=True, translate=True)
    print = fields.Boolean('Print')
    order_id = fields.Many2one("sale.order", string="Sale order", index=True)

    def get_print_properties(self):
        if use_product_description:
            return False
        return [x.name.id for x in self if x.print]
