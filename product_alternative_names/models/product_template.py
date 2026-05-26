# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import fields, models, _

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    alt_name = fields.Char('Alternative name', translate=True, help="Please fill the alternative name for this product")

    def write(self, vals):
        if 'alt_name' in vals:
            value = []
            for template in self:
                for p in template.product_variant_ids:
                    value.append((1, p.id, {'alt_name': vals['alt_name']}))
                vals['product_variant_ids'] = value
        return super(ProductTemplate, self).write(vals)
