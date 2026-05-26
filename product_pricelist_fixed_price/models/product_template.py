# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import fields, models, _, api

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pricelist_item_ids = fields.One2many(
        'product.pricelist.item',
        compute='_compute_pricelist_item_ids',
        inverse='_inverse_pricelist_item_ids'
    )
    variant_pricelist_item_ids = fields.One2many(
        'product.pricelist.item',
        compute='_compute_variant_pricelist_item_ids',
        inverse='_inverse_variant_pricelist_item_ids'
    )
    category_pricelist_item_ids = fields.One2many(
        'product.pricelist.item',
        compute='_compute_category_pricelist_item_ids',
        inverse='_inverse_category_pricelist_item_ids',
    )

    def _compute_pricelist_item_ids(self):
        for product_tmpl in self:
            product_tmpl.pricelist_item_ids = self.env['product.pricelist.item'].search([
                ('applied_on', '=', '1_product'),
                ('product_tmpl_id', '=', product_tmpl.id),
                ('compute_price', '=', 'fixed'),
            ])

    def _inverse_pricelist_item_ids(self):
        for product_tmpl in self:
            old_pricelist_item_ids = self.env['product.pricelist.item'].search([
                ('applied_on', '=', '1_product'),
                ('product_tmpl_id', '=', product_tmpl.id),
                ('compute_price', '=', 'fixed'),
            ])
            for product_list_item in product_tmpl.pricelist_item_ids:
                if not product_list_item.id:
                    self.env['product.pricelist.item'].create({
                        'pricelist_id': product_list_item.pricelist_id.id,
                        'applied_on': '1_product',
                        'product_tmpl_id': product_tmpl.id,
                        'categ_id': False,
                        'product_id': False,
                        'compute_price': 'fixed',
                        'fixed_price': product_list_item.fixed_price,
                        'date_start': product_list_item.date_start,
                        'date_end': product_list_item.date_end,
                        'min_quantity': product_list_item.min_quantity,
                    })
            (old_pricelist_item_ids - product_tmpl.pricelist_item_ids).unlink()

    def _compute_variant_pricelist_item_ids(self):
        for product_tmpl in self:
            product_tmpl.variant_pricelist_item_ids = self.env['product.pricelist.item'].search([
                ('applied_on', '=', '0_product_variant'),
                ('product_id', 'in', product_tmpl.product_variant_ids.ids),
                ('compute_price', '=', 'fixed'),
            ])

    def _inverse_variant_pricelist_item_ids(self):
        for product_tmpl in self:
            old_pricelist_item_ids = self.env['product.pricelist.item'].search([
                ('applied_on', '=', '0_product_variant'),
                ('product_id', 'in', product_tmpl.product_variant_ids.ids),
                ('compute_price', '=', 'fixed'),
            ])
            for product_list_item in product_tmpl.variant_pricelist_item_ids:
                if not product_list_item.id:
                    self.env['product.pricelist.item'].create({
                        'pricelist_id': product_list_item.pricelist_id.id,
                        'applied_on': '0_product_variant',
                        'product_tmpl_id': False,
                        'categ_id': False,
                        'product_id': product_list_item.product_id.id,
                        'compute_price': 'fixed',
                        'fixed_price': product_list_item.fixed_price,
                        'date_start': product_list_item.date_start,
                        'date_end': product_list_item.date_end,
                        'min_quantity': product_list_item.min_quantity,
                    })
            (old_pricelist_item_ids - product_tmpl.pricelist_item_ids).unlink()

    @api.depends('categ_id')
    def _compute_category_pricelist_item_ids(self):
        for product_tmpl in self:
            product_tmpl.category_pricelist_item_ids = self.env['product.pricelist.item'].search([
                ('applied_on', '=', '2_product_category'),
                ('categ_id', '=', product_tmpl.categ_id.id),
                ('compute_price', '=', 'fixed'),
            ])

    def _inverse_category_pricelist_item_ids(self):
        for product_tmpl in self:
            old_pricelist_item_ids = self.env['product.pricelist.item'].search([
                ('applied_on', '=', '2_product_category'),
                ('categ_id', '=', product_tmpl.categ_id.id),
                ('compute_price', '=', 'fixed'),
            ])
            for product_list_item in product_tmpl.category_pricelist_item_ids:
                if not product_list_item.id:
                    self.env['product.pricelist.item'].create({
                        'pricelist_id': product_list_item.pricelist_id.id,
                        'applied_on': '2_product_category',
                        'product_tmpl_id': False,
                        'categ_id': product_list_item.categ_id.id,
                        'product_id': False,
                        'compute_price': 'fixed',
                        'fixed_price': product_list_item.fixed_price,
                        'date_start': product_list_item.date_start,
                        'date_end': product_list_item.date_end,
                        'min_quantity': product_list_item.min_quantity,
                    })
            (old_pricelist_item_ids - product_tmpl.pricelist_item_ids).unlink()
