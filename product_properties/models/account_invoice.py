# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    use_product_description = fields.Boolean(default=True)
    print_properties = fields.One2many('product.properties.print', 'invoice_id', 'Print properties')
    #print_properties = fields.One2many('product.properties.print', 'partner_id', related='partner_id.print_properties', string='Print properties')

    ## bug Velimira report 26-08-2019
    #@api.multi
    #@api.onchange('partner_id', 'company_id')
    #def _onchange_partner_id(self):
    #    for invoice in self:
    #        if invoice.partner_id.print_properties:
    #            values = []
    #            for line in self.env['product.properties.print'].search([('system_properties', '=', True)]):
    #                compare = order.print_properties.filtered(lambda r: r.name == line.name)
    #                if compare:
    #                    values.append((1, compare.id, {'name': line.name, 'print': line.print}))
    #                else:
    #                    values.append((0, False, {'name': line.name, 'print': line.print, 'order_id': order.id}))
    #            for line in invoice.partner_id.print_properties:
    #                compare = invoice.print_properties.filtered(lambda r: r.name == line.name)
    #                if compare:
    #                    values.append((1, compare.id, {'name': line.name, 'print': line.print}))
    #                else:
    #                    values.append((0, False, {'name': line.name, 'print': line.print, 'order_id': invoice.id}))
    #            if values:
    #                invoice.update({'print_properties': values})
    #    return super(AccountInvoice, self).ensure_one()._onchange_partner_id()

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    has_propertis = fields.Boolean(compute="_get_has_propertis")

    def _get_has_propertis(self):
        for rec in self:
            rec.has_propertis = len(rec.invoice_id.print_properties.ids) > 0
