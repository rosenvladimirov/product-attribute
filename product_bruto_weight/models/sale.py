# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bruto_weight = fields.Float('Bruto Weight', compute="_compute_bruto_weight", digits=dp.get_precision('Stock Weight'),
        help="Bruto Weight of the products, packaging is included. The unit of measure can be changed in the general settings")
    weight = fields.Float('Nett Weight', compute="_compute_weight", digits=dp.get_precision('Stock Weight'),
        help="Nett Weight of the products, packaging is included. The unit of measure can be changed in the general settings")
    product_tray = fields.Integer('Consumable products/tray', related='product_packaging.product_tray')
    per_layrs = fields.Integer('Trays per layer', related="product_packaging.per_layrs")
    europallet_lears = fields.Integer('Layers per europallet', related="product_packaging.europallet_lears")

    @api.one
    @api.depends('product_packaging', 'product_packaging.weight', 'product_packaging.bruto_weight', 'product_uom_qty')
    def _compute_bruto_weight(self):
        self.bruto_weight = self.product_packaging.bruto_weight*self.product_uom_qty

    @api.one
    @api.depends('product_packaging', 'product_packaging.weight', 'product_packaging.bruto_weight', 'product_uom_qty')
    def _compute_weight(self):
        self.weight = self.product_packaging.weight*self.product_uom_qty

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res.update({'product_packaging': self.product_packaging.id})
        return res

    @api.onchange('product_packaging')
    @api.depends('product_id')
    def product_packaging_change(self):
        res = {}
        self.secondary_uom_id = self.product_packaging.secondary_uom_id or self.product_id.sale_secondary_uom_id
        if self.secondary_uom_id:
            self.secondary_uom_qty = 1.0
            self.onchange_secondary_uom()
        return res