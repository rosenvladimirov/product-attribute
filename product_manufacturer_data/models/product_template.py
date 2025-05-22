# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    manufacturer_ids = fields.One2many(
        'product.manufacturer',
        'product_tmpl_id',
        'Manufacturers'
    )
    manufacturer_id = fields.Many2one('product.manufacturer',
                                      'Manufacturer',
                                      compute='_compute_manufacturer_id',
                                      help='Technical fields for reels')


    @api.depends('manufacturer_ids')
    def _compute_manufacturer_id(self):
        for record in self:
            if len(record.manufacturer_ids) > 0:
                record.manufacturer_id = record.manufacturer_ids[0]
            else:
                record.manufacturer_id = False
