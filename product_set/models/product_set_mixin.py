#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _, Command

_logger = logging.getLogger(__name__)


class ProductSetsMixin(models.AbstractModel):
    _name = 'product.set.mixin'
    _description = "Product set Mixin"

    product_set_id = fields.Many2one('product.set', string='Product set')
    product_set_line_id = fields.Many2one('product.set.line', string='Product set line')
    product_set_qty = fields.Float('Product set quantity')
    product_set_price_subtotal = fields.Float('Product set price subtotal')

    @staticmethod
    def _get_update_product_set_section_values(total_quantity):
        return {
            'product_set_qty': total_quantity['section_quantity']/total_quantity['quantity'],
            'product_set_price_subtotal': total_quantity['amount'],
        }

    def _add_product_set_sections(self, model, vals_list):
        inx = None
        model = model and model or 'purchase.order'
        for sequence_inx, vals in enumerate(vals_list):
            order_id = self.env[model].search([('id', '=', vals['order_id'])], limit=1)
            if order_id.order_line:
                last_section_id = order_id.order_line[-1]
                sequence = last_section_id.sequence
                vals.update({'sequence': sequence + 2 + sequence_inx})
                product_set_id = last_section_id.product_set_id
                if product_set_id:
                    set_line_ids = product_set_id.set_line_ids
                    if vals.get('product_id') in set_line_ids.mapped('product_id').ids:
                        product_set_line_id = set_line_ids. \
                            filtered(lambda p: p.product_id.id == vals.get('product_id'))
                        if len(product_set_line_id) > 1:
                            product_set_line_id = product_set_line_id[0]
                        vals.update({
                            'product_set_id': product_set_id.id,
                            'product_set_line_id': len(product_set_line_id) > 1 and product_set_line_id[
                                0].id or product_set_line_id.id,
                            'product_set_section_id': last_section_id.id,
                        })
                    elif vals.get('product_id') and inx is None:
                        inx = sequence_inx
        return vals_list

    def _set_product_set_sections(self, model, values):
        model = model and model or 'purchase.order'

        for record in self:
            order_id = record.order_id
            sequences = {}
            line_section = {}
            sequence_inx_insert = 0
            for sequence_inx, line in enumerate(order_id.order_line. \
                                                    sorted(lambda r: f"{r.product_set_id or 0}-{r.sequence}",
                                                           reverse=True)):
                product_set_id = line.product_set_id
                sequences.update({line: sequence_inx + sequence_inx_insert})
                if line.product_set_id and not line.product_set_line_id:
                    set_line_ids = product_set_id.set_line_ids
                    if line.product_id.id in set_line_ids.mapped('product_id').ids:
                        product_set_line_id = set_line_ids. \
                            filtered(lambda p: p.product_id.id == line.product_id.id)
                        if len(product_set_line_id) > 1:
                            product_set_line_id = product_set_line_id[0]
                        line.with_context(**dict(self._context, create_new_set=True)).write({
                            'product_set_line_id': product_set_line_id.id
                        })
                if product_set_id and line.product_set_id != product_set_id:
                    sequence_inx_insert += 1
                    line_section.update({line: sequence_inx + sequence_inx_insert})
            for line, sequence_inx in sequences.items():
                line.with_context(**dict(self._context, create_new_set=True)).write({
                    'sequence': sequence_inx
                })
            for line, sequence_inx in line_section.items():
                values_to_add = {
                    'display_type': 'line_section',
                    'name': _('Uncategorized'),
                    'order_id': order_id.id,
                    'sequence': sequence_inx,
                }
                # _logger.info(f"Set section {values_to_add}")
                self.env[model].create(values_to_add)
        return values

    def _unlink_product_set_sections(self, field_name=False):
        field_name = field_name or 'order_id'
        for record in self:
            if self._context.get('create_new_set') or not record.display_type == 'line_section':
                continue
            product_set_section_id = record
            for order_id in record.mapped(field_name):
                order_lines = order_id.order_line. \
                               filtered(lambda r: r.product_set_section_id.id == product_set_section_id.id)
                for line in order_lines:
                    line.unlink()
