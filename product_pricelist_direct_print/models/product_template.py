# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
#from odoo.addons.muk_dms_field.fields import dms_fields

import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.template"

    def check_for_price(self, pricelist, date):
        pricelist_items = self.item_ids | self.product_variant_ids.mapped('pricelist_item_ids')
        ids = [x.product_id.id for x in pricelist_items if x.product_id and pricelist.id == x.pricelist_id.id and (x.compute_price == 'fixed' and x.fixed_price > 0.0)]
        #_logger.info("PRICELISTITEMS %s:%s" % (pricelist_items, ids))
        if pricelist_items and any([x.id in ids for x in self.product_variant_ids]):
            return True
        return any([x.check_for_price(pricelist, date) for x in self.product_variant_ids])
