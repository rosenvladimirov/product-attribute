# -*- coding: utf-8 -*-
# dXFactory Proprietary License (dXF-PL) v1.0. See LICENSE file for full copyright and licensing details.

import itertools
import psycopg2

from odoo.addons import decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, except_orm
from odoo.tools import pycompat

import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    description_short = fields.Char("Short description", translate=True)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if name:
            quants = self.env['stock.quant.package'].search([('name', operator, name)]).mapped('quant_ids')
            if quants:
                ids = set([x.product_id.id for x in quants])
                products = self.search([('id', 'in', list(ids))] + args or [], limit=limit)
                #_logger.info("Search ----- %s:%s:%s" % (args, quants, products))
                if products:
                    return products.name_get()

        if name and len([x for x in filter(lambda y: y[0] in ('description_short', 'product_tmpl_id.description_short'), args)]) == 0:
            products = self.search([('description_short', operator, name)] + args or [], limit=limit)
            if not products:
                products = self.search([('product_tmpl_id.description_short', operator, name)] + args or [], limit=limit)
            if products:
                return products.name_get()
        return super(ProductProduct, self).name_search(name=name, args=args, operator=operator, limit=limit)
