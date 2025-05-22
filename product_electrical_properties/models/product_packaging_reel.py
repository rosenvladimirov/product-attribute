# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from copy import deepcopy

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ProductPackagingReel(models.Model):
    _name = 'product.packaging.reel'
    _inherits = {'product.packaging': 'package_id'}
    _description = 'Reel Packaging'

    package_id = fields.Many2one(
        'product.packaging',
        'Packages',
        ondelete="cascade",
        required=True,
        index=True
    )
    manufacturer_id = fields.Many2one(
        'product.manufacturer',
        'Manufacturer',
        required=True,
        ondelete="cascade",
        index=True,
    )
    diameter = fields.Float('Diameter')
    size = fields.Integer('Width')
    step = fields.Integer('Length')
    thickness = fields.Float('Thickness')
    volume_type_id = fields.Many2one('product.packaging.type', string='Reel Volume type')
    volume_type = fields.Selection(related="volume_type_id.volume_type")

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('manufacturer_id'):
                manufacturer_id = self.env['product.manufacturer'].browse(values['manufacturer_id'])
                values['product_id'] = manufacturer_id.product_id and \
                                       manufacturer_id.product_id.id or \
                                       manufacturer_id.product_tmpl_id.product_variant_id.id
            _logger.info(f"values {values}")
        return super().create(vals_list)

    def unlink(self):
        if not self._context.get('block_unlink'):
            for record in self:
                record.package_id.unlink()
        return super().unlink()
