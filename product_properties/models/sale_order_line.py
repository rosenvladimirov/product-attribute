#  -*- coding: utf-8 -*-
#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    has_properties = fields.Boolean(compute="_get_has_properties")

    def _get_has_properties(self):
        for rec in self:
            rec.has_properties = len(rec.order_id.print_properties.ids) > 0 \
                                 and (len(rec.product_id.product_properties_ids.ids) > 0
                                      or len(rec.product_id.tmpl_product_properties_ids.ids) > 0)

    # def _prepare_invoice_line(self, **optional_values):
    #     vals = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
    #     if self.order_id.print_properties:
    #         vals['print_properties'] = self.order_id.print_properties.ids
    #     return vals
