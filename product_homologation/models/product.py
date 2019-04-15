# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
#from odoo.addons.muk_dms_field.fields import dms_fields

import logging
_logger = logging.getLogger(__name__)

class Product(models.Model):
    _inherit = 'product.product'

    homologation_variant = fields.Char('Homologation', help="Plase fill the Homologation code", translate=True)

    @api.onchange('homologation_variant')
    def _on_change_homologation_variant(self):
        if self.product_tmpl_id.homologation:
            self.product_tmpl_id.homologation = ""
