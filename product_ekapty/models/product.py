# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
#from odoo.addons.muk_dms_field.fields import dms_fields

import logging
_logger = logging.getLogger(__name__)

class Product(models.Model):
    _inherit = 'product.product'

    ekapty_variant = fields.Char('EKAPTY', help="Plase fill the EKAPTY code")

    @api.onchange('ekapty_variant')
    def _on_change_ekapty_variant(self):
        if self.product_tmpl_id.ekapty_variant:
            self.product_tmpl_id.ekapty_variant = ""
