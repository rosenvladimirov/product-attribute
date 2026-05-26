# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class ProductSetPropertiesLineCategorySet(models.TransientModel):
    _name = 'product.set.properties.category.line.set'
    _description = 'Wizard for set category line product set properties'

    wiz_id = fields.Many2one('product.set.properties.category.set', 'Category properties Wizard')
    categ_id = fields.Many2one('product.properties.category', string='Wizard Category Properties')
    applicability = fields.Selection(related='categ_id.applicability')
    lines_ids = fields.One2many(related='categ_id.lines_ids')
