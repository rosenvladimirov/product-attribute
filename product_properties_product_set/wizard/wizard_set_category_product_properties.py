# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import models, fields, api, Command, _

_logger = logging.getLogger(__name__)


class ProductSetPropertiesCategorySet(models.TransientModel):
    _name = 'product.set.properties.category.set'
    _description = 'Wizard for set category product set properties'

    category_product_properties_ids = fields.Many2many(
        'product.properties.category',
        'category_properties_set_category_set_rel',
        string='Default properties category'
    )
    empty_properties = fields.Boolean('Remove all old properties')
    product_set_ids = fields.Many2many(
        'product.set',
        'product_set_properties_category_set_rel',
        string='Product Sets'
    )
    wiz_line_ids = fields.One2many(
        'product.set.properties.category.line.set',
        'wiz_id',
        'Lines'
    )

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('active_model') == 'product.set' and not res.get('product_set_ids'):
            res['product_set_ids'] = self.env['product.set'].browse(self._context.get('active_ids', [])).ids
        return res

    @api.onchange('category_product_properties_ids')
    def onchange_category_product_properties_ids(self):
        for record in self:
            for category in self.category_product_properties_ids:
                if not record.wiz_line_ids.filtered(lambda r: r.categ_id == category):
                    record.wiz_line_ids |= self.env['product.set.properties.category.line.set'].create({
                        'categ_id': category.id,
                        'applicability': category.applicability,
                        'lines_ids': [Command.set(category.lines_ids.ids)],
                        'wiz_id': record.id,
                    })

    def action_set_category_product_properties(self):
        for record in self:
            _logger.info(f'empty_properties {record.empty_properties}\n'
                         f'category_product_properties_ids {record.category_product_properties_ids}\n')
            if record.empty_properties:
                for product_set_id in record.product_set_ids:
                    product_set_id.properties_category_ids = False
                    product_set_id.product_properties_ids = False

            if record.category_product_properties_ids:
                for product_set_id in record.product_set_ids:
                    # _logger.info(f'category_product_properties_ids mapped: {record.mapped("category_product_properties_ids").ids}')
                    product_set_id.write({
                        'properties_category_ids': [Command.set(record.mapped('category_product_properties_ids').ids)],
                        'product_properties_ids': self.env['product.properties'].
                        _get_default_product_properties_ids(record.mapped('category_product_properties_ids'),
                                                            product_set_id),
                    })
