# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def copy(self, default=None):
        self.ensure_one()
        ctx = dict(self.env.context)
        ctx.pop('manufacturer_id', self.product_id.manufacturer_id.id)
        self = self.with_context(ctx)
        return super(PurchaseOrder, self).copy(default=default)

    def _prepare_supplier_info(self, partner, line, price, currency):
        res = super()._prepare_supplier_info(partner, line, price, currency)
        res.update({
            'manufacturer_id': line.manufacturer_id.id,
        })
        return res

    def _add_supplier_to_product(self):
        ctx = dict(self.env.context)
        ctx.pop('manufacturer_id', self.product_id.manufacturer_id.id)
        self = self.with_context(ctx)
        return super(PurchaseOrder, self)._add_supplier_to_product()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _get_domain_manufacturer_id(self):
        return self.product_id and ['|', ('product_id', '=', self.product_id.id), ('product_id', '=', False),
                                    ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)] or []

    manufacturer_id = fields.Many2one("product.manufacturer",
                                      "Factory Product",
                                      domain=lambda self: self._get_domain_manufacturer_id())
    supplierinfo_id = fields.Many2one("product.supplierinfo", "Supplierinfo")

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
