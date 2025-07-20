# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import models, fields, api, Command, _

_logger = logging.getLogger(__name__)


class ProductPropertiesCategorySet(models.TransientModel):
    _name = 'product.properties.category.set'
    _description = 'Wizard for set category product properties'

    category_product_properties_ids = fields.Many2many(
        'product.properties.category',
        'category_properties_category_set_rel',
        string='Default properties category'
    )
    empty_properties = fields.Boolean('Remove all old properties')
    product_tmpl_ids = fields.Many2many(
        'product.template',
        'product_tmpl_properties_category_set_rel',
        string='Products'
    )
    product_ids = fields.Many2many(
        'product.product',
        'product_properties_category_set_rel',
        string='Product Variants'
    )
    wiz_line_ids = fields.One2many(
        'product.properties.category.line.set',
        'wiz_id',
        'Lines'
    )

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('active_model') == 'product.product' and not res.get('product_ids'):
            res['product_ids'] = self.env['product.product'].browse(self._context.get('active_ids', [])).ids
        if self._context.get('active_model') == 'product.template' and not res.get('product_tmpl_ids'):
            res['product_tmpl_ids'] = self.env['product.template'].browse(self._context.get('active_ids', [])).ids
        return res

    @api.onchange('category_product_properties_ids')
    def onchange_category_product_properties_ids(self):
        for record in self:
            for category in self.category_product_properties_ids:
                if not record.wiz_line_ids.filtered(lambda r: r.categ_id == category):
                    record.wiz_line_ids |= self.env['product.properties.category.line.set'].create({
                        'categ_id': category.id,
                        'applicability': category.applicability,
                        'lines_ids': [Command.set(category.lines_ids.ids)],
                        'wiz_id': record.id,
                    })

    def action_set_category_product_properties(self):
        for record in self:
            _logger.info(f'empty_properties {record.empty_properties}\n'
                         f'category_product_properties_ids {record.category_product_properties_ids}\n'
                         f'product_tmpl_ids: {record.product_tmpl_ids}\n')
            if record.empty_properties:
                for product_tmpl_id in record.product_tmpl_ids:
                    product_tmpl_id.properties_category_ids = False
                    product_tmpl_id.product_properties_ids = False
                    if product_tmpl_id.product_variant_count > 0:
                        for product in product_tmpl_id.product_variant_ids:
                            product.properties_category_ids = False
                            product.product_properties_ids = False

            if record.category_product_properties_ids:
                category_product_properties_ids = record.mapped("category_product_properties_ids")
                for product_tmpl_id in record.product_tmpl_ids:
                    product_tmpl_id.with_delay().set_category_product_properties(category_product_properties_ids)
                # for product_tmpl_id in record.product_tmpl_ids:
                #     _logger.info(f'category_product_properties_ids mapped: {record.mapped("category_product_properties_ids").ids}')
                #     product_tmpl_id.write({
                #         'properties_category_ids': [Command.set(record.mapped('category_product_properties_ids').ids)],
                #         'product_properties_ids': self.env['product.properties'].
                #         _get_default_product_properties_ids(record.mapped('category_product_properties_ids'),
                #                                             product_tmpl_id),
                #     })
                #     if product_tmpl_id.product_variant_count > 0:
                #         applicability = self.env['product.properties.category'].search(
                #             [('applicability', '=', 'product')])
                #         if applicability:
                #             for product in product_tmpl_id.product_variant_ids:
                #                 if len(product.product_properties_ids.ids) == 0:
                #                     product.write({
                #                         'properties_category_ids': [Command.set(applicability.ids)],
                #                         'product_properties_ids': self.env['product.properties'].
                #                         _get_default_product_properties_ids(applicability, product)
                #                     })

                for product_id in record.product_ids:
                    product_id.with_delay().set_category_product_properties(category_product_properties_ids)
                    # product_id.write({
                    #     'properties_category_ids': [Command.set(record.mapped('category_product_properties_ids').ids)],
                    #     'product_properties_ids': self.env['product.properties'].
                    #     _get_default_product_properties_ids(record.mapped('category_product_properties_ids'), product_id)
                    # })
