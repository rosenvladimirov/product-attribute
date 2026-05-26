# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductCategory(models.Model):
    _inherit = "product.category"

    category_pricelist_item_ids = fields.One2many(
        'product.pricelist.item',
        compute='_compute_category_pricelist_item_ids',
        inverse='_inverse_category_pricelist_item_ids'
    )

    def _compute_category_pricelist_item_ids(self):
        for category in self:
            category.category_pricelist_item_ids = self.env['product.pricelist.item'].search([
                ('applied_on', '=', '2_product_category'),
                ('categ_id', '=', category.id),
                ('compute_price', '=', 'fixed'),
            ])

    def _inverse_category_pricelist_item_ids(self):
        for category in self:
            old_category_pricelist_item_ids = category.category_pricelist_item_ids
            for product_list_item in category.category_pricelist_item_ids:
                if not product_list_item.id:
                    self.env['product.pricelist.item'].create({
                        'pricelist_id': product_list_item.pricelist_id.id,
                        'applied_on': '2_product_category',
                        'categ_id': category.id,
                        'product_tmpl_id': False,
                        'product_id': False,
                        'compute_price': 'fixed',
                        'fixed_price': product_list_item.fixed_price,
                        'date_start': product_list_item.date_start,
                        'date_end': product_list_item.date_end,
                        'min_quantity': product_list_item.min_quantity,
                    })
            (old_category_pricelist_item_ids - category.category_pricelist_item_ids).unlink()
