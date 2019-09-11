# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class SystemProductProperties(models.TransientModel):
    _name = 'system.product.properties'

    name = fields.Many2one('product.properties.category.lines', 'Property name', required=True)
    lines_ids = fields.Many2many('system.product.properties.lines', string='Category properties')
    product_id = fields.Many2one('product.product')

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.lines_ids = [(6, False, [x.id for x in self.name])]
        return {}

    def action_transfer(self):
        if self.product_id:
            self.product_id.update({})
        return {
            "type": "ir.actions.do_nothing",
        }


class PurchaseManufacturerSupplierLine(models.TransientModel):
    _name = 'system.product.properties.lines'

    pp_category_line_id = fields.Many2one('product.properties.category.lines', 'Category line')
    pp_name = fields.Many2one("product.properties.type", string="Property name", related="pp_category_line_id.name")
