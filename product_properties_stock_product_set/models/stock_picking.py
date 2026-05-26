# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, _, api, Command, fields, models


class Picking(models.Model):
    _inherit = "stock.picking"

    def _get_print_product_set_data(self):
        super()._get_print_product_set_data()
        for record in self:
            if record.use_product_set == 'reset':
                record.move_line_ids.filtered(lambda r: r.move_id.product_set_id). \
                    write({'show_details': True})
            elif record.use_product_set == 'closed':
                record.move_line_ids.filtered(lambda r: r.move_id.product_set_id). \
                    write({'show_details': False})
            elif record.use_product_set == 'collapse':
                record.move_line_ids.filtered(lambda r: r.move_id.product_set_id). \
                    write({'show_details': False})
            elif record.use_product_set == 'expand':
                record.move_line_ids.filtered(lambda r: r.move_id.product_set_id). \
                    write({'show_details': True})
