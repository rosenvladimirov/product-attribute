# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import models, fields, api, _, Command

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "product.properties.print.mixin"]

    products_properties_env_ref = fields.Char(default='product_properties.report_stock_picking_html')
    print_properties = fields.One2many('product.properties.print',
                                       'picking_id',
                                       'Print properties',
                                       copy=False)

    def picking_set_all_print_properties(self):
        self.ensure_one()
        self.set_all_print_properties(self, lines='move_ids')

    def picking_set_products_print_properties(self):
        self.ensure_one()
        self.set_products_print_properties(self, lines='move_ids')

    def picking_set_partner_print_properties(self):
        self.ensure_one()
        self.set_partner_print_properties(self.partner_id, self, target_field_name='picking_id')

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super().create(vals_list)
    #     for vals in vals_list:
    #         if 'product_prop_static_id' not in vals:
    #             res.write({
    #                 'product_prop_static_id': self.env['product.properties.static'].
    #                 static_property_data(res, vals)['product_prop_static_id']
    #             })
    #     return res
    #
    # def write(self, vals):
    #     # Check if 'product_prop_static_id' is not in vals
    #     if 'product_prop_static_id' not in vals:
    #         for record in self:
    #             # If product_prop_static_id is not set, generate or update it
    #             if not record.product_prop_static_id:
    #                 # Get the data for product.properties.static
    #                 property_data = self.env['product.properties.static'].static_property_data(
    #                     record, vals, product_variant_id=False, force_backport=True
    #                 )
    #
    #                 # Update or create the product_prop_static_id field
    #                 if 'product_prop_static_id' in record._fields:
    #                     record.write({'product_prop_static_id': property_data.get('product_prop_static_id')})
    #                 else:
    #                     # If product_prop_static_id is not a field, you may need to handle it differently
    #                     # For example, you might need to use a different field or association
    #                     pass

        # Call the super method to complete the write operation
        # return super(Picking, self).write(vals)

    ###################################################### OLD CODE
    # def write(self, vals):
    #     if 'product_prop_static_id' not in vals:
    #         for record in self:
    #             if not record.product_prop_static_id:
    #                 vals = self.env['product.properties.static'].static_property_data(record, vals)
    #     return super(Picking, self).write(vals)
