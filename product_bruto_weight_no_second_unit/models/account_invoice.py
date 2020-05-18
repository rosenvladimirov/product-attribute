# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    bruto_weight = fields.Float('Bruto Weight', compute="_compute_bruto_weight", digits=dp.get_precision('Stock Weight'),
        help="Bruto Weight of the products, packaging is included. The unit of measure can be changed in the general settings")
    weight = fields.Float('Nett Weight', compute="_compute_weight", digits=dp.get_precision('Stock Weight'),
        help="Nett Weight of the products, packaging is included. The unit of measure can be changed in the general settings")
    product_tray = fields.Integer('Consumable products/tray', related='product_id.product_tray')
    per_layrs = fields.Integer('Trays per layer', related="product_id.per_layrs")
    europallet_lears = fields.Integer('Layers per europallet', related="product_id.europallet_lears")

    @api.one
    @api.depends('product_id', 'product_id.weight', 'product_id.bruto_weight', 'quantity')
    def _compute_bruto_weight(self):
        self.bruto_weight = self.product_id.bruto_weight*self.quantity

    @api.one
    @api.depends('product_id', 'product_id.weight', 'product_id.bruto_weight', 'quantity')
    def _compute_weight(self):
        self.weight = self.product_id.weight*self.quantity
