# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    has_properties = fields.Boolean(compute="_get_has_properties")

    def _get_has_properties(self):
        for rec in self:
            rec.has_properties = \
                len(rec.picking_id.print_properties.ids) > 0 \
                and (len(rec.product_id.product_properties_ids.ids) > 0
                     or len(rec.product_id.tmpl_product_properties_ids.ids) > 0)

    def _get_aggregated_product_quantities(self, **kwargs):
        def get_aggregated_properties(move_line=False, move=False):
            move = move or move_line.move_id
            uom = move.product_uom or move_line.product_uom_id
            name = move.product_id.display_name
            description = move.description_picking
            if description == name or description == move.product_id.name:
                description = False
            product = move.product_id
            line_key = f"{product.id}_{product.display_name}_" f'{description or ""}_{uom.id}'
            return line_key

        aggregated_move_lines = super(
            StockMoveLine, self
        )._get_aggregated_product_quantities(**kwargs)
        for move_line in self:
            line_key = get_aggregated_properties(move_line=move_line)
            if line_key in aggregated_move_lines:
                aggregated_move_lines[line_key]["move_line"] = move_line
        return aggregated_move_lines
