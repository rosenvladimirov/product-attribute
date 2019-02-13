# Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    manufacturer = fields.Many2one(
        comodel_name='res.partner', string='Manufacturer',
    )
    manufacturer_pname = fields.Char(string='Manuf. Product Name')
    manufacturer_pref = fields.Char(string='Manuf. Product Code')
    manufacturer_purl = fields.Char(string='Manuf. Product URL')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        # Only use the product.product heuristics if there is a search term and the domain
        # does not specify a match on `product.template` IDs.
        if not name or any(term[0] == 'id' for term in (args or [])):
            return super(ProductTemplate, self).name_search(name=name, args=args, operator=operator, limit=limit)

        #_logger.info("Search _________ %s" % args)
        Product = self.env['product.product']
        templates = self.browse([])
        if name and len([x for x in filter(lambda y: y[0] in ('manufacturer_pref'), args)]) == 0:
            products = Product.search([('manufacturer_pref', operator, name)] + args or [], limit=limit)
            if not products:
                products = templates.search([('manufacturer_pref', operator, name)] + args or [], limit=limit)
            if products:
                return products.name_get()
        return super(ProductTemplate, self).name_search(
            '', args=[('id', 'in', list(set(templates.ids)))],
            operator='ilike', limit=limit)
