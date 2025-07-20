# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class ProductPropertiesSetAll(models.TransientModel):
    _name = 'product.properties.set.all'
    _description = 'Wizard for set all product properties'

    category_print_properties = fields.Many2one('product.properties.print.category', 'Default Print properties category')
    use_partner = fields.Boolean('Use partner properties')
    empty_properties = fields.Boolean('Remove all old properties')

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if not res.get('empty_properties'):
            object_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
            res['empty_properties'] = object_id.print_properties.ids != []
        return res

    def set_all_print_properties(self):
        active_id = self._context['active_id']
        active_model = self._context.get('active_model')

        if active_model and id:
            mode = []
            ctx = self._context.copy()
            if self.category_print_properties:
                mode.append('category')
            if self.use_partner:
                mode.append('partner')
            if mode:
                ctx = dict(ctx, mode_print_properties=mode)
            ex_obj = self.env[active_model].browse([active_id])
            if ex_obj:
                if self.empty_properties:
                    ex_obj.remove_all_print_properties()
                ex_obj.category_print_properties = self.category_print_properties
                # set_all_print_properties(self, record, lines=False)
                lines = False
                if ex_obj._name in ['sale.order', 'purchase.order']:
                    lines = 'order_line'
                elif ex_obj._name == 'stock.picking':
                    lines = 'move_ids'
                elif ex_obj._name == 'account.move':
                    lines = 'invoice_line_ids'
                ex_obj.with_context(ctx).set_all_print_properties(ex_obj, lines=lines, mode=mode)
        return {'type': 'ir.actions.act_window_close'}
