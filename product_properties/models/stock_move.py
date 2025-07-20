# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    has_properties = fields.Boolean(compute="_get_has_properties")

    def _get_has_properties(self):
        for rec in self:
            rec.has_properties = \
                len(rec.picking_id.print_properties.ids) > 0 \
                and (len(rec.product_id.product_properties_ids.ids) > 0
                     or len(rec.product_id.tmpl_product_properties_ids.ids) > 0)
