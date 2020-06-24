# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    #use_product_description = fields.Boolean(default=True)
    use_product_properties = fields.Selection([
        ('description', _('Use descriptions')),
        ('properties', _('Use properties')),],
        string="Type product description",
        help='Choice type of the view for product description',
        default="description")
    print_properties = fields.One2many('product.properties.print', 'invoice_id', 'Print properties')
    category_print_properties = fields.Many2one('product.properties.print.category', 'Default Print properties category')
    product_prop_static_id = fields.Many2one("product.properties.static", 'Static Product properties')
    invoice_sub_type = fields.Many2one(related="product_prop_static_id.invoice_sub_type")

    #print_properties = fields.One2many('product.properties.print', 'partner_id', related='partner_id.print_properties', string='Print properties')
    @api.multi
    def remove_all_print_properties(self):
        for record in self:
            record.print_properties =  False

    @api.multi
    def set_all_print_properties(self):
        for record in self:
            record.print_properties = self.env['product.properties'].set_all_print_properties(record, record.invoice_line_ids)

    @api.multi
    def set_partner_print_properties(self):
        for record in self:
            print_properties = []
            partner = record.partner_id.parent_id and record.partner_id.parent_id or record.partner_id
            partner_static_print_ids = [x.static_field for x in partner.print_properties if x.print and x.static_field and x.static_field not in self.env['product.properties.static'].ignore_fields()]
            if partner.print_properties and not record.print_properties:
                print_properties += [(0, False, {'name': x.name.id, 'invoice_id': self.id, 'print': True, 'sequence': x.sequence}) for x in partner.print_properties if x.name and not x.static_field]
                if partner_static_print_ids:
                    print_properties += [(0, False, {'static_field': x, 'invoice_id': self.id, 'print': True, 'sequence': 9999}) for x in partner_static_print_ids]
                record.print_properties = print_properties

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        partner = self.partner_id.parent_id and self.partner_id.parent_id or self.partner_id
        if partner.print_properties:
            self.print_properties = False
            self.set_partner_print_properties()
        return res

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        vals = self.env['product.properties.static'].static_property_data(res, vals)
        partner = self.partner_id.parent_id and self.partner_id.parent_id or self.partner_id
        if partner.print_properties:
            self.set_partner_print_properties()
        return res

    @api.multi
    def write(self, vals):
        if 'product_prop_static_id' not in vals:
            for record in self:
                vals = self.env['product.properties.static'].static_property_data(record, vals)
        return super(AccountInvoice, self).write(vals)


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    has_propertis = fields.Boolean(compute="_get_has_propertis")

    def _get_has_propertis(self):
        for rec in self:
            rec.has_propertis = len(rec.invoice_id.print_properties.ids) > 0
