# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
#from odoo.addons.muk_dms_field.fields import dms_fields

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    specifications = fields.Text('Specification', translate=True, help="Please fill the specifications for this product")

    #@api.onchange('specifications')
    #@api.depends('product_variant_ids')
    #def _onchange_specifications(self):
    #    if self.specifications:
    #        value = []
    #        for p in self.product_variant_ids:
    #            value.append((1, p.id, {'specifications': self.specifications}))
    #        self.product_variant_ids = value
    #        for p in self.product_variant_ids:
    #            _logger.info("VARIANT %s:%s" % (p.specifications, self.specifications))

    @api.multi
    def write(self, vals):
        if 'specifications' in vals:
            value = []
            for template in self:
                for p in template.product_variant_ids:
                    value.append((1, p.id, {'specifications': vals['specifications']}))
                vals['product_variant_ids'] = value
        return super(ProductTemplate, self).write(vals)
