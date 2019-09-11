# Copyright 2018 Tecnativa - Vicent Cubells
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'


    def _risk_margin_selection(self):
        ret = super(ProductPricelist, self)._risk_margin_selection()
        if ret:
            ret.append('supplierinfo')
            return ret
        return ['supplierinfo']

    def _rule_compute_price(self, rule):
        ret = super(ProductPricelist, self)._rule_compute_price(rule)
        if not ret:
            return rule.compute_price == 'formula' and rule.base == 'supplierinfo'
        else:
            return ret

    def _rule_compute_price_base_on(self, rule, products_qty_partner):
        price = super(ProductPricelist, self)._rule_compute_price_base_on(rule, products_qty_partner)
        for product, qty, _partner in products_qty_partner:
            if rule.compute_price == 'formula' and rule.base == 'supplierinfo':
                context = self.env.context
                price = product._get_competitorinfo_pricelist_price(
                        rule,
                        date=date or context.get('date', fields.Date.today()),
                        quantity=qty,)
        return price


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    base = fields.Selection(
        selection_add=[
            ('supplierinfo', 'Prices based on supplier info'),
        ],
    )
    no_supplierinfo_min_quantity = fields.Boolean(
        string='Ignore Supplier Info Min. Quantity',
    )

