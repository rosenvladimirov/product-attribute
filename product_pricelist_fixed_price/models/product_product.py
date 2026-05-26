# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import fields, models, _

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    pricelist_item_ids = fields.One2many(
        'product.pricelist.item',
        compute='_compute_pricelist_item_ids',
        inverse='_inverse_pricelist_item_ids'
    )

    def _compute_pricelist_item_ids(self):
        for product in self:
            product.pricelist_item_ids = self.env['product.pricelist.item'].search([
                ('applied_on', '=', '0_product_variant'),
                ('product_id', '=', product.id),
                ('compute_price', '=', 'fixed'),
            ])

    def _inverse_pricelist_item_ids(self):
        for product in self:
            old_pricelist_item_ids = self.env['product.pricelist.item'].search([
                ('applied_on', '=', '0_product_variant'),
                ('product_id', '=', product.id),
                ('compute_price', '=', 'fixed'),
            ])
            for product_list_item in product.pricelist_item_ids:
                if not product_list_item.id:
                    self.env['product.pricelist.item'].create({
                        'pricelist_id': product_list_item.pricelist_id.id,
                        'applied_on': '0_product_variant',
                        'categ_id': False,
                        'product_tmpl_id': False,
                        'product_id': product.id,
                        'compute_price': 'fixed',
                        'fixed_price': product_list_item.fixed_price,
                        'date_start': product_list_item.date_start,
                        'date_end': product_list_item.date_end,
                        'min_quantity': product_list_item.min_quantity,
                    })
            (old_pricelist_item_ids - product.pricelist_item_ids).unlink()
