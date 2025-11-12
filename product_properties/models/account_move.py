# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from collections import defaultdict
from odoo import api, fields, models, _, Command
from odoo.tools import float_compare, float_is_zero, formatLang

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "product.properties.print.mixin"]

    products_properties_env_ref = fields.Char(default='product_properties.report_account_move_html')
    print_properties = fields.One2many(
        'product.properties.print',
        'invoice_id',
        'Print properties',
        copy=False
    )

    def invoice_set_all_print_properties(self):
        self.ensure_one()
        self.set_all_print_properties(self, lines='invoice_line_ids')

    def invoice_set_products_print_properties(self):
        self.ensure_one()
        self.set_products_print_properties(self, lines='invoice_line_ids')

    def invoice_set_partner_print_properties(self):
        self.ensure_one()
        self.set_partner_print_properties(self.partner_id, self, target_field_name='invoice_id')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        partner = self.partner_id.parent_id and self.partner_id.parent_id or self.partner_id
        if partner.print_properties:
            self.print_properties = False
            self.set_partner_print_properties(self.partner_id, self, target_field_name='invoice_id')
        return res

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super().create(vals_list)
    #     for account_move_id, vals in zip(res, vals_list):
    #         if 'product_prop_static_id' not in vals:
    #             values = self.env['product.properties.static'].static_property_data(res, vals)['product_prop_static_id']
    #             account_move_id.write({
    #                 'product_prop_static_id': values,
    #             })
    #         partner_id = account_move_id.partner_id
    #         if partner_id.partner_id:
    #             partner_id = partner_id.parent_id
    #         if partner_id and partner_id.print_properties:
    #             account_move_id.set_partner_print_properties()
    #     return res
    #
    # def write(self, vals):
    #     if 'product_prop_static_id' not in vals:
    #         for record in self:
    #             if not record.product_prop_static_id:
    #                 vals = self.env['product.properties.static'].static_property_data(record, vals)
    #     return super(AccountInvoice, self).write(vals)
