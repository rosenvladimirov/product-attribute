#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import models, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_print_product_set_data(self):
        super()._get_print_product_set_data()
        for record in self:
            if record.use_product_set == 'reset':
                record.invoice_line_ids.filtered(lambda r: r.display_type == 'line_section'). \
                    write({'show_details': True})
            elif record.use_product_set == 'closed':
                record.invoice_line_ids.filtered(lambda r: r.display_type == 'line_section'). \
                    write({'show_details': False})
            elif record.use_product_set == 'collapse':
                record.invoice_line_ids.filtered(lambda r: r.display_type == 'line_section' and not r.product_set_id). \
                    write({'show_details': True})
                record.invoice_line_ids.filtered(lambda r: r.display_type == 'line_section' and r.product_set_id). \
                    write({'show_details': False})
            elif record.use_product_set == 'expand':
                record.invoice_line_ids.filtered(lambda r: r.display_type == 'line_section' and not r.product_set_id). \
                    write({'show_details': True})
                record.invoice_line_ids.filtered(lambda r: r.display_type == 'line_section' and r.product_set_id). \
                    write({'show_details': True})


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_values_product_set_mixin(self, total_quantity):
        values = super()._get_values_product_set_mixin(total_quantity)
        if self.move_id.use_product_set != 'manual':
            values.update({
                "show_details": self.move_id.use_product_set == 'collapse',
            })
        return values

    def get_print_taxes(self):
        invoice_line_ids = self.move_id.mapped('invoice_line_ids').\
            filtered(lambda r: r.product_set_section_id == self)
        return list(set(map(lambda x: (x.description or x.name), invoice_line_ids.mapped('tax_ids'))))
