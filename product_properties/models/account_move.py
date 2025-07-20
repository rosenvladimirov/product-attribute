# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from itertools import groupby
from odoo import api, fields, models, _, Command

import logging

from odoo.tools import float_compare, float_is_zero, formatLang

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "product.properties.print.mixin"]

    products_properties_env_ref = fields.Char(default='product_properties.report_account_move_html')
    print_properties = fields.One2many('product.properties.print',
                                       'invoice_id',
                                       'Print properties',
                                       copy=False)

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


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    has_properties = fields.Boolean(compute="_get_has_properties")

    def _get_has_properties(self):
        for rec in self:
            rec.has_properties = len(rec.move_id.print_properties.ids) > 0 \
                                    and (len(rec.product_id.product_properties_ids.ids) > 0
                                      or len(rec.product_id.tmpl_product_properties_ids.ids) > 0)

    def _get_invoiced_lot_values(self):
        """ Get and prepare data to show a table of invoiced lot on the invoice's report. """
        self.ensure_one()
        res = []
        if self.move_id.state == 'draft' or not self.move_id.invoice_date or self.move_id.move_type not in ('out_invoice', 'out_refund'):
            return res

        current_invoice_amls = self.filtered(lambda aml: aml.display_type == 'product' and aml.product_id and aml.product_id.type in ('consu', 'product') and aml.quantity)
        all_invoices_amls = current_invoice_amls.sale_line_ids.invoice_lines.filtered(lambda aml: aml.move_id.state == 'posted').sorted(lambda aml: (aml.date, aml.move_name, aml.id))
        index = all_invoices_amls.ids.index(current_invoice_amls[:1].id) if current_invoice_amls[:1] in all_invoices_amls else 0
        previous_amls = all_invoices_amls[:index]
        invoiced_qties = current_invoice_amls._get_invoiced_qty_per_product()
        invoiced_products = invoiced_qties.keys()

        if self.move_type == 'out_invoice':
            # filter out the invoices that have been fully refund and re-invoice otherwise, the quantities would be
            # consumed by the reversed invoice and won't be print on the new draft invoice
            previous_amls = previous_amls.filtered(lambda aml: aml.move_id.payment_state != 'reversed')

        previous_qties_invoiced = previous_amls._get_invoiced_qty_per_product()

        if self.move_type == 'out_refund':
            # we swap the sign because it's a refund, and it would print negative number otherwise
            for p in previous_qties_invoiced:
                previous_qties_invoiced[p] = -previous_qties_invoiced[p]
            for p in invoiced_qties:
                invoiced_qties[p] = -invoiced_qties[p]

        qties_per_lot = defaultdict(float)
        previous_qties_delivered = defaultdict(float)
        stock_move_lines = current_invoice_amls.sale_line_ids.move_ids.move_line_ids.filtered(lambda sml: sml.state == 'done' and sml.lot_id).sorted(lambda sml: (sml.date, sml.id))
        for sml in stock_move_lines:
            if sml.product_id not in invoiced_products or 'customer' not in {sml.location_id.usage, sml.location_dest_id.usage}:
                continue
            product = sml.product_id
            product_uom = product.uom_id
            qty_done = sml.product_uom_id._compute_quantity(sml.qty_done, product_uom)

            # is it a stock return considering the document type (should it be it thought of as positively or negatively?)
            is_stock_return = (
                    self.move_type == 'out_invoice' and (sml.location_id.usage, sml.location_dest_id.usage) == ('customer', 'internal')
                    or
                    self.move_type == 'out_refund' and (sml.location_id.usage, sml.location_dest_id.usage) == ('internal', 'customer')
            )
            if is_stock_return:
                returned_qty = min(qties_per_lot[sml.lot_id], qty_done)
                qties_per_lot[sml.lot_id] -= returned_qty
                qty_done = returned_qty - qty_done

            previous_qty_invoiced = previous_qties_invoiced[product]
            previous_qty_delivered = previous_qties_delivered[product]
            # If we return more than currently delivered (i.e., qty_done < 0), we remove the surplus
            # from the previously delivered (and qty_done becomes zero). If it's a delivery, we first
            # try to reach the previous_qty_invoiced
            if float_compare(qty_done, 0, precision_rounding=product_uom.rounding) < 0 or \
                    float_compare(previous_qty_delivered, previous_qty_invoiced, precision_rounding=product_uom.rounding) < 0:
                previously_done = qty_done if is_stock_return else min(previous_qty_invoiced - previous_qty_delivered, qty_done)
                previous_qties_delivered[product] += previously_done
                qty_done -= previously_done

            qties_per_lot[sml.lot_id] += qty_done

        for lot, qty in qties_per_lot.items():
            # access the lot as a superuser in order to avoid an error
            # when a user prints an invoice without having the stock access
            lot = lot.sudo()
            if float_is_zero(invoiced_qties[lot.product_id], precision_rounding=lot.product_uom_id.rounding) \
                    or float_compare(qty, 0, precision_rounding=lot.product_uom_id.rounding) <= 0:
                continue
            invoiced_lot_qty = min(qty, invoiced_qties[lot.product_id])
            invoiced_qties[lot.product_id] -= invoiced_lot_qty
            res.append({
                'product_name': lot.product_id.display_name,
                'quantity': formatLang(self.env, invoiced_lot_qty, dp='Product Unit of Measure'),
                'uom_name': lot.product_uom_id.name,
                'lot_name': lot.name,
                # The lot id is needed by localizations to inherit the method and add custom fields on the invoice's report.
                'lot_id': lot.id,
            })

        return res
