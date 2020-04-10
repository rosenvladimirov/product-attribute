# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    #description_short = fields.Char("Short description", size=19, translate=True)

    variant_seller_ids = fields.One2many('product.supplierinfo', 'product_id')
    default_variant_seller_id = fields.Many2one('product.supplierinfo', 'Choice default label')
    label_name = fields.Char(string="Label name", related="default_variant_seller_id.product_name", store=True)
    label_code = fields.Char(string="Label code", related="default_variant_seller_id.product_code", store=True)
    display_label_name = fields.Char(compute='_compute_label_name', store=False)

    @api.depends('label_name', 'label_code')
    def _compute_label_name(self):
        for product in self:
            if product.label_name and product.label_code:
                product.display_label_name = "[%s] %s" % (product.label_code, product.label_name)
            elif product.label_name and not product.label_code:
                product.display_label_name = product.label_name
            elif not product.label_name and product.label_code:
                product.display_label_name = "[%s] %s" % (product.label_code, product.display_name)
            else:
                product.display_label_name = product.display_name

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if name and args:
            attr = self.env["product.attribute.line"].name_search(name=name)
            ids = [x[0] for x in attr]
            if ids:
                product_template = self.env['product.template'].search([('attribute_line_ids', 'in', ids)])
                domain = [('product_tmpl_id', 'in', [x.id for x in product_template])]
                products = self.search(domain, limit=limit)
                if products:
                    return products.name_get()
            if name and len([x for x in filter(lambda y: y[0] in ('manufacturer_pref'), args)]) == 0:
                Product = self.env['product.product']
                products = Product.search(["|" for x in range(1, len(args))]+[('manufacturer_pref', operator, name)]+args, limit=limit)
                if products:
                    return products.name_get()
        return super(ProductProduct, self).name_search(name=name, args=args, operator=operator, limit=limit)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    #description_short = fields.Char("Short description", size=19, translate=True)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not name:
            return super(ProductTemplate, self).name_search(name=name, args=args, operator=operator, limit=limit)
        attr = self.env["product.attribute.line"].name_search(name=name)
        ids = [x[0] for x in attr]
        #_logger.info("Filter %s:%s:%s" % (ids, name, args))
        if ids:
            super(ProductTemplate, self).name_search(name="", args=[('id', 'in', ids)], operator='ilike', limit=limit)
        Product = self.env['product.product']
        templates = self.browse([])
        if name and len([x for x in filter(lambda y: y[0] in ('manufacturer_pref'), args)]) == 0:
            # ["|" for x in range(1, len(args))]
            products = Product.search([('manufacturer_pref', operator, name)]+args, limit=limit)
            if products:
                return products.name_get()
        return super(ProductTemplate, self).name_search(name=name, args=args, operator=operator, limit=limit)
