# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    use_product_description = fields.Boolean(default=True)
    print_properties = fields.One2many('product.properties.print', 'order_id', 'Print properties')
    #print_properties = fields.One2many('product.properties.print', 'partner_id', related='partner_id.print_properties', string='Print properties')
    products_properties = fields.Html('Products properties', compute="_get_products_properties")

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for order in self:
            if order.partner_id.print_properties:
                values = []
                for line in order.partner_id.print_properties:
                    compare = order.print_properties.filtered(lambda r: r.name == line.name)
                    if compare:
                        values.append((1, compare.id, {'name': line.name, 'print': line.print}))
                    else:
                        values.append((0, False, {'name': line.name, 'print': line.print, 'order_id': order.id}))
                if values:
                    order.update({'print_properties': values})
                else:
                    order.update({'print_properties': False})
        return super(SaleOrder, self).onchange_partner_id()

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        rcontext['doc'] = self
        result['html'] = self.env.ref(
            'product_properties.report_saleorder_html').with_context(context).render(
                rcontext)
        return result

    @api.multi
    def _get_products_properties(self):
        for rec in self:
            if len(rec.order_line.ids) > 0:
                rec.products_properties = rec._get_html()['html']


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    has_propertis = fields.Boolean(compute="_get_has_propertis")

    def _get_has_propertis(self):
        for rec in self:
            rec.has_propertis = len(rec.order_id.print_properties.ids) > 0

    @api.multi
    def _prepare_invoice_line(self, qty):
        vals = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        if self.order_id.print_properties:
            vals['print_properties'] = self.order_id.print_properties.ids
        return vals
