# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    print_properties = fields.One2many('product.properties.print', 'picking_id', 'Print properties')
    category_print_properties = fields.Many2one('product.properties.print.category', 'Default Print properties category')
    #use_product_description = fields.Boolean(default=True)
    use_product_properties = fields.Selection([
        ('description', _('Use descriptions')),
        ('properties', _('Use properties')),],
        string="Type product description",
        help='Choice type of the view for product description',
        default="description")
    product_prop_static_id = fields.Many2one("product.properties.static", 'Static Product properties')
    invoice_sub_type = fields.Many2one(related="product_prop_static_id.invoice_sub_type")

    @api.multi
    def remove_all_print_properties(self):
        for record in self:
            record.print_properties =  False

    @api.multi
    def set_all_print_properties(self):
        for record in self:
            record.print_properties = self.env['product.properties'].set_all_print_properties(record, record.move_lines)

    @api.model
    def create(self, vals):
        res = super(Picking, self).create(vals)
        vals = self.env['product.properties.static'].static_property_data(res, vals)
        return res

    @api.multi
    def write(self, vals):
        if 'product_prop_static_id' not in vals:
            for record in self:
                vals = self.env['product.properties.static'].static_property_data(record, vals)
        return super(Picking, self).write(vals)
