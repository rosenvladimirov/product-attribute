# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, fields, models, Command

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "product.properties.print.mixin"]

    products_properties_env_ref = fields.Char(default='product_properties.report_sale_order_html')
    print_properties = fields.One2many('product.properties.print',
                                       'sale_id',
                                       'Print properties',
                                       copy=False)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for record in self:
            if record.partner_id.print_properties:
                record.set_partner_print_properties(record.partner_id, record, target_field_name='sale_id')

    def sale_set_all_print_properties(self):
        self.ensure_one()
        self.set_all_print_properties(self, lines='order_line')

    def sale_set_partner_print_properties(self):
        self.ensure_one()
        self.set_partner_print_properties(self.partner_id, self, target_field_name='sale_id')

    def sale_set_products_print_properties(self):
        self.ensure_one()
        self.set_products_print_properties(self, lines='order_line')

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res['print_properties'] = self.print_properties.ids
        return res
