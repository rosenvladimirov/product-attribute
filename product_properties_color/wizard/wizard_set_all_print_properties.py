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

    @api.multi
    def set_all_print_properties(self):
        id = self._context['active_id']
        obj = self._context.get('obj_name')
        if obj and id:
            mode = []
            ctx = self._context.copy()
            if self.category_print_properties:
                mode.append('category')
            if self.use_partner:
                mode.append('partner')
            if mode:
                ctx = dict(ctx, mode_print_properties=mode)
            ex_obj = self.env[obj].browse([id])
            if ex_obj:
                if self.empty_properties:
                    ex_obj.remove_all_print_properties()
                ex_obj.category_print_properties = self.category_print_properties
                ex_obj.with_context(ctx).set_all_print_properties()
        return {'type': 'ir.actions.act_window_close'}
