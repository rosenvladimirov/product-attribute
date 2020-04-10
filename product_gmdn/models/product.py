# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
#from odoo.addons.muk_dms_field.fields import dms_fields

import logging
_logger = logging.getLogger(__name__)

class Product(models.Model):
    _inherit = 'product.product'

    gmdn_variant = fields.Char('Global Medical Device Nomenclature (GMDN)', translate=True, help="Plase fill the Medical GDMN code")

    @api.onchange('gmdn_variant')
    def _on_change_gmdn_variant(self):
        if self.product_tmpl_id.gmdn_variant:
            self.product_tmpl_id.gmdn_variant = ""
