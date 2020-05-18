# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    product_tray = fields.Integer('Consumable products/tray', related='product_id.product_tray')
    per_layrs = fields.Integer('Trays per layer', related="product_id.per_layrs")
    europallet_lears = fields.Integer('Layers per europallet', related="product_id.europallet_lears")
