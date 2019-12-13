# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
#from odoo.addons.muk_dms_field.fields import dms_fields

import logging
_logger = logging.getLogger(__name__)

class Product(models.Model):
    _inherit = 'product.product'

    default_code_external = fields.Char('External Reference')

    @api.onchange('default_code_external')
    def _on_change_default_code_external(self):
        if self.product_tmpl_id.default_code_external and len(self.product_tmpl_id.product_variant_ids) > 1 and self.default_code_external:
            self.product_tmpl_id.default_code_external = ""
