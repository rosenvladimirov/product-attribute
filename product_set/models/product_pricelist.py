#  Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, _


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _get_applicable_rules_domain(self, products, date, **kwargs):
        domain = super(Pricelist, self)._get_applicable_rules_domain(products, date, **kwargs)
        if self._context.get('product_set_id'):
            domain.append(
                ['|', ('product_set_id', '=', self._context['product_set_id']), ('product_set_id', '=', False)])
        return domain
