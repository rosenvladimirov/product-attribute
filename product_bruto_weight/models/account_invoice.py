# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        data.update({'product_packaging': line.product_packaging.id})
        return data


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    product_packaging = fields.Many2one('product.packaging', string='Product Packaging')
    bruto_weight = fields.Float('Bruto Weight', compute="_compute_bruto_weight", digits=dp.get_precision('Stock Weight'),
        help="Bruto Weight of the products, packaging is included. The unit of measure can be changed in the general settings")
    weight = fields.Float('Nett Weight', compute="_compute_weight", digits=dp.get_precision('Stock Weight'),
        help="Nett Weight of the products, packaging is included. The unit of measure can be changed in the general settings")
    product_tray = fields.Integer('Consumable products/tray', related='product_packaging.product_tray')
    per_layrs = fields.Integer('Trays per layer', related="product_packaging.per_layrs")
    europallet_lears = fields.Integer('Layers per europallet', related="product_packaging.europallet_lears")

    @api.one
    @api.depends('product_packaging', 'product_packaging.weight', 'product_packaging.bruto_weight', 'quantity')
    def _compute_bruto_weight(self):
        self.bruto_weight = self.product_packaging.bruto_weight*self.quantity

    @api.one
    @api.depends('product_packaging', 'product_packaging.weight', 'product_packaging.bruto_weight', 'quantity')
    def _compute_weight(self):
        self.weight = self.product_packaging.weight*self.quantity
