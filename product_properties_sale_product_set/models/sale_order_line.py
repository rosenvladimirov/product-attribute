#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import models, api, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_print_product_set_data(self):
        super()._get_print_product_set_data()
        for record in self:
            if record.use_product_set == 'reset':
                record.order_line.filtered(lambda r: r.display_type == 'line_section'). \
                    write({'show_details': True})
            elif record.use_product_set == 'closed':
                record.order_line.filtered(lambda r: r.display_type == 'line_section'). \
                    write({'show_details': False})
            elif record.use_product_set == 'collapse':
                record.order_line.filtered(lambda r: r.display_type == 'line_section' and r.product_set_id). \
                    write({'show_details': False})
            elif record.use_product_set == 'expand':
                record.order_line.filtered(lambda r: r.display_type == 'line_section' and r.product_set_id). \
                    write({'show_details': True})


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_values_product_set_mixin(self, total_quantity):
        values = super()._get_values_product_set_mixin(total_quantity)
        if self.order_id.use_product_set != 'manual':
            values.update({
                "show_details": self.order_id.use_product_set == 'collapse',
            })
        # _logger.info(f"Show detail: {values}")
        return values

    def get_print_taxes(self):
        order_line = self.order_id.mapped('order_line').\
            filtered(lambda r: r.product_set_section_id == self)
        return list(set(map(lambda x: (x.description or x.name), order_line.mapped('tax_id'))))
