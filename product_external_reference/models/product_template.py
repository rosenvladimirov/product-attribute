# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
#from odoo.addons.muk_dms_field.fields import dms_fields

import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.template"

    default_code_external = fields.Char('External Reference', compute='_compute_default_code_external', inverse='_set_default_code_external', store=True)

    @api.depends('product_variant_ids', 'product_variant_ids.default_code_external')
    def _compute_default_code_external(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.default_code_external = template.product_variant_ids.default_code_external
        for template in (self - unique_variants):
            template.default_code_external = ''

    @api.one
    def _set_default_code_external(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.default_code_external = self.default_code_external
