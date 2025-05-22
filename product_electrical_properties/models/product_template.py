# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # short_description = fields.Char(
    #     'Technical Description',
    #     size=40,
    #     compute='_compute_short_description',
    #     inverse='_inverse_short_description',
    #     store=True
    # )
    component_type_id = fields.Many2one(
        'component.definition.properties',
        compute='_compute_component_type_id',
        inverse='_inverse_component_type_id',
        string='Component Type',
        store=True
    )
    component_properties = fields.Properties(
        'Component technical data',
        compute='_compute_component_properties',
        inverse='_inverse_component_properties',
        definition='component_type_id.component_properties_definition',
        store=True,
    )
    reelpackaging_ids = fields.One2many(
        'product.packaging.reel',
        compute='_compute_reelpackaging_ids',
        inverse='_inverse_reelpackaging_ids',
        search='_search_reelpackaging_ids',
        string='Standard Product Packages',
    )


    @api.depends('manufacturer_ids')
    def _compute_manufacturer_id(self):
        for record in self:
            if len(record.manufacturer_ids) > 0:
                record.manufacturer_id = record.manufacturer_ids[0]
            else:
                record.manufacturer_id = False

    @api.depends('product_variant_ids.reelpackaging_ids')
    def _compute_reelpackaging_ids(self):
        for record in self:
            record.reelpackaging_ids = record.product_variant_ids.mapped('reelpackaging_ids')

    def _inverse_reelpackaging_ids(self):
        for record in self:
            for product_id in record.product_variant_ids:
                product_id.write({'reelpackaging_ids': [(6, 0, record.reelpackaging_ids.ids)]})

    def _search_reelpackaging_ids(self, operator, value):
        return [('product_variant_ids.reelpackaging_ids', operator, value)]

    @api.depends('product_variant_id.component_type_id')
    def _compute_component_type_id(self):
        for record in self:
            record.component_type_id = record.product_variant_id.component_type_id

    def _inverse_component_type_id(self):
        for record in self:
            for product_id in record.product_variant_ids:
                if product_id.component_type_id != record.component_type_id:
                    product_id.write({'component_properties': False})
                product_id.component_type_id = record.component_type_id

    @api.depends('product_variant_ids.component_properties')
    def _compute_component_properties(self):
        for record in self:
            if record.product_variant_id:
                record.component_properties = record.product_variant_id.component_properties

    def _inverse_component_properties(self):
        for record in self:
            if record.product_variant_count == 1 and \
                    record.component_properties and \
                    record.component_properties != record.product_variant_id.component_properties:
                for product_id in record.product_variant_ids:
                    product_id.write({'component_properties': record.component_properties})

    # @api.depends('product_variant_ids.short_description')
    # def _compute_short_description(self):
    #     for record in self:
    #         if record.product_variant_id:
    #                 record.short_description = record.product_variant_id.short_description

    # def _inverse_short_description(self):
    #     for record in self:
    #         if record.product_variant_count == 1 and \
    #                 record.short_description and \
    #                 record.short_description != record.product_variant_id.short_description:
    #             for product_id in record.product_variant_ids:
    #                 product_id.write({'short_description': record.short_description})

    def action_update_nextar_data(self):
        for record in self:
            for product_id in record.product_variant_ids:
                product_id.action_update_nextar_data()
