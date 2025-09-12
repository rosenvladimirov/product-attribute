#  Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductCategory(models.Model):
    _inherit = "product.category"

    product_set_count = fields.Integer(
        '# Product sets', compute='_compute_product_set_count',
        help="The number of product sets under this category (Does not consider the children categories)")

    def _compute_product_set_count(self):
        read_group_res = self.env['product.set'].read_group([('categ_id', 'child_of', self.ids)], ['categ_id'],
                                                            ['categ_id'])
        group_data = dict((data['categ_id'][0], data['categ_id_count']) for data in read_group_res)
        for categ in self:
            product_set_count = 0
            for sub_categ_id in categ.search([('id', 'child_of', categ.ids)]).ids:
                product_set_count += group_data.get(sub_categ_id, 0)
            categ.product_set_count = product_set_count
