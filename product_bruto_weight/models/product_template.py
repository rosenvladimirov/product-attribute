# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.template"

    bruto_weight = fields.Float('Bruto Weight', compute='_compute_bruto_weight', digits=dp.get_precision('Bruto Stock Weight'),
        inverse='_set_bruto_weight', store=True,
        help="The bruto weight of the contents in Kg, not including any packaging, etc.")


    @api.depends('product_variant_ids', 'product_variant_ids.bruto_weight')
    def _compute_bruto_weight(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.bruto_weight = template.product_variant_ids.bruto_weight
        for template in (self - unique_variants):
            template.bruto_weight = 0.0

    @api.one
    def _set_bruto_weight(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.bruto_weight = self.bruto_weight
