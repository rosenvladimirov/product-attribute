# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'


    def _risk_margin_selection(self):
        ret = super(ProductPricelist, self)._risk_margin_selection()
        if ret:
            ret.append('competitorinfo')
            return ret
        return ['competitorinfo']

    def _rule_compute_price(self, rule):
        ret = super(ProductPricelist, self)._rule_compute_price(rule)
        if not ret:
            return rule.compute_price == 'formula' and rule.base == 'supplierinfo'
        else:
            return ret

    def _rule_compute_price_base_on(self, rule, products_qty_partner):
        price = super(ProductPricelist, self)._rule_compute_price_base_on(rule, products_qty_partner)
        for product, qty, _partner in products_qty_partner:
            if rule.compute_price == 'formula' and rule.base == 'competitorinfo':
                context = self.env.context
                price = product._get_supplierinfo_pricelist_price(
                        rule,
                        date=date or context.get('date', fields.Date.today()),
                        quantity=qty,)
        return price

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    base = fields.Selection(
        selection_add=[
            ('competitorinfo', 'Prices based on competitor info'),
        ],
    )
