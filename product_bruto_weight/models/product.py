# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = 'product.product'

    bruto_weight = fields.Float('Brut weight', digits=dp.get_precision('Stock Weight'),
        help="Bruto Weight of the product, packaging not included. The unit of measure can be changed in the general settings")


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    nett_weight = fields.Float('Nett Weight', digits=dp.get_precision('Stock Weight'),
        help="Nett Weight of the package to add. The unit of measure can be changed in the general settings")
    bruto_weight = fields.Float('Bruto Weight', digits=dp.get_precision('Stock Weight'), compute="_compute_bruto_weight",
        help="Bruto Weight of the product, packaging are included. The unit of measure can be changed in the general settings")
    weight = fields.Float('Weight', digits=dp.get_precision('Stock Weight'), compute="_compute_weight",
        help="Nett Weight of the products, packaging not included. The unit of measure can be changed in the general settings")
    product_tray = fields.Integer('Consumable products/tray')
    per_layrs = fields.Integer('Trays per layer')
    europallet_lears = fields.Integer('Layers per europallet')
    secondary_uom_id = fields.Many2one('product.secondary.unit', string='Secondary Unit of Measure',
                                        help='Default Secondary Unit of Measure.',)
    secondary_qty = fields.Float('Contained Quantity', related="secondary_uom_id.factor",
                                 help="The total number of products you can have per pallet or box.")

    @api.one
    @api.depends('product_id', 'product_id.weight', 'product_id.bruto_weight', 'nett_weight', 'qty')
    def _compute_bruto_weight(self):
        self.bruto_weight = self.product_id.bruto_weight*self.qty + self.nett_weight

    @api.one
    @api.depends('product_id', 'product_id.weight', 'qty')
    def _compute_weight(self):
        self.weight = self.product_id.weight*self.qty
