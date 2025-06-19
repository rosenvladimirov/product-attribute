# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ProductManufacturer(models.Model):
    _inherit = "product.manufacturer"

    packaging_ids = fields.One2many(
        'product.packaging',
        string='Manufacturer product Packages',
        compute="_compute_packaging_ids",
        inverse="_set_packaging_ids",
        search="_search_packaging_ids",
        help="Gives the different ways to manufacturer package the same product variant."
    )
    tmpl_packaging_ids = fields.One2many(
        'product.packaging',
        string="Manufacturer template Packages",
        compute="_compute_tmpl_packaging_ids",
        inverse="_set_tmpl_packaging_ids",
        search="_search_tmpl_packaging_ids",
        help="Gives the different ways to manufacturer package the same product templates."
    )

    def _compute_tmpl_packaging_ids(self):
        for record in self:
            record.tmpl_packaging_ids = record.product_tmpl_id.packaging_ids

    def _set_tmpl_packaging_ids(self):
        for record in self:
            record.product_tmpl_id.packaging_ids = record.tmpl_packaging_ids

    def _search_tmpl_packaging_ids(self, operator, value):
        ids = self.env['product.packaging'].search(
            [
                ('name', operator, value),
                ('product_id', '=', self.product_variant_id.id)
            ]
        )
        return [('id', 'in', ids)]

    def _compute_packaging_ids(self):
        for record in self:
            record.packaging_ids = record.product_tmpl_id.packaging_ids

    def _set_packaging_ids(self):
        for record in self:
            record.product_id.packaging_ids = record.packaging_ids

    def _search_packaging_ids(self, operator, value):
        ids = self.env['product.packaging'].search([('name', operator, value), ('product_id', '=', self.product_id.id)])
        return [('id', 'in', ids)]
