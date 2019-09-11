# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import api, models, fields


class PurchaseManufacturerSupplier(models.TransientModel):
    _name = 'purchase.manufacturer.supplier'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template', string="Template", required=True)
    variant_line_ids = fields.Many2many(
        comodel_name='sale.manage.variant.line', string="Variant Lines")
    only_supplier = fields.Boolean("Show only for PO vendor")


class PurchaseManufacturerSupplierLine(models.TransientModel):
    _name = 'purchase.manufacturer.supplier.line'

    value_x = fields.Many2one(comodel_name='product.attribute.value')
    value_y = fields.Many2one(comodel_name='product.attribute.value')
    product_uom_qty = fields.Float(
        string="Quantity", digits=dp.get_precision('Product UoS'))
