# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom,
                               location_id, name, origin, values, group_id):
        res = super(StockRule, self)._get_stock_move_values(
            product_id, product_qty, product_uom, location_id, name, origin,
            values, group_id
        )
        if values.get('sale_line_id', False):
            sale_line = self.env['sale.order.line'].browse(
                values['sale_line_id'])
            if sale_line.product_packaging:
                res.update({
                    'product_packaging': sale_line.product_packaging.id,
                })
        return res
