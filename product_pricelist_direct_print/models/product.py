# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
#from odoo.addons.muk_dms_field.fields import dms_fields

import logging
_logger = logging.getLogger(__name__)

class Product(models.Model):
    _inherit = 'product.product'

    def check_for_price(self, pricelist, date):
        product = self
        ids = [x.product_id.id for x in product.pricelist_item_ids if pricelist.id == x.pricelist_id.id]
        #_logger.info("PRICELISTITEMS %s:%s" % (pricelist_items, ids))
        if product.pricelist_item_ids and product.id in ids:
            return True
        price_extra = 0.0
        for attribute_price in product.mapped('attribute_value_ids.price_ids'):
            if attribute_price.product_tmpl_id == product.product_tmpl_id:
                price_extra += attribute_price.price_extra
        if price_extra == 0.0:
            # check for price in pricelist
            return False
        return True
