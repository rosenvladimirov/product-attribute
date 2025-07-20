# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models, Command
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "product.properties.print.mixin"]

    products_properties_env_ref = fields.Char(default='product_properties.report_purchase_order_html')
    print_properties = fields.One2many('product.properties.print',
                                       'purchase_id',
                                       'Print properties',
                                       copy=False)
    invoice_sub_type = fields.Many2one("product.properties.static.dropdown",
                                       related="print_properties.invoice_sub_type")

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.ensure_one()
        if self.partner_id.print_properties:
            values = []
            for line in self.partner_id.print_properties:
                compare = self.print_properties.filtered(lambda r: r.name == line.name)
                if compare:
                    values.append(Command.update(
                        compare.id,
                        {
                            'name': line.name,
                            'print': line.print
                        }))
                else:
                    values.append(Command.create({
                        'name': line.name,
                        'print': line.print,
                        'purchase_id': self.id
                    }))
            if values:
                self.update({'print_properties': values})
            else:
                self.update({'print_properties': False})
        return super().onchange_partner_id()

    def purchase_set_all_print_properties(self):
        self.ensure_one()
        self.set_all_print_properties(self, lines='order_line')

    def purchase_set_partner_print_properties(self):
        self.ensure_one()
        self.set_partner_print_properties(self.partner_id, self, target_field_name='purchase_id')

    def purchase_set_products_print_properties(self):
        self.ensure_one()
        self.set_products_print_properties(self, lines='order_line')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    has_properties = fields.Boolean(compute="_get_has_properties")

    def _get_has_properties(self):
        for rec in self:
            rec.has_properties = len(rec.order_id.print_properties.ids) > 0 \
                                 and (len(rec.product_id.product_properties_ids.ids) > 0
                                      or len(rec.product_id.tmpl_product_properties_ids.ids) > 0)

    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     res = {}
    #     if res.get('domain', False):
    #         res['domain'].update({
    #             'manufacturer_id': [
    #                 '|', ('product_id', '=', self.product_id.id),
    #                 ('product_id', '=', False),
    #                 ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)
    #             ]})
    #         res = super(PurchaseOrderLine, self).onchange_product_id()
    #     return res

    # @api.onchange('product_qty', 'product_uom', 'manufacturer_id')
    # def _onchange_quantity(self):
    #     if not self.product_id:
    #         return
    #
    #     seller = self.product_id.with_context(
    #         dict(self._context, manufacturer_id=self.manufacturer_id.id))._select_seller(
    #         partner_id=self.partner_id,
    #         quantity=self.product_qty,
    #         date=self.order_id.date_order and self.order_id.date_order[:10],
    #         uom_id=self.product_uom)
    #
    #     if seller or not self.date_planned:
    #         self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #
    #     if not seller:
    #         return
    #
    #     price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price,
    #                                                                          self.product_id.supplier_taxes_id,
    #                                                                          self.taxes_id,
    #                                                                          self.company_id) if seller else 0.0
    #     if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
    #         price_unit = seller.currency_id.compute(price_unit, self.order_id.currency_id)
    #
    #     if seller and self.product_uom and seller.product_uom != self.product_uom:
    #         price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)
    #
    #     self.price_unit = price_unit
    #     if seller:
    #         self.supplierinfo_id = seller.id
    #         # self.manufacturer_id = seller.manufacturer_id.id
