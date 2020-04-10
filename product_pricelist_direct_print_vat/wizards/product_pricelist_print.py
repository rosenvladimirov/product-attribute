# Copyright 2017 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import numpy as np
import pandas as pd

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class ProductPricelistPrint(models.TransientModel):
    _name = 'product.pricelist.print'

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
    )
    categ_ids = fields.Many2many(
        comodel_name='product.category',
        string='Categories',
    )
    show_variants = fields.Boolean()
    product_tmpl_ids = fields.Many2many(
        comodel_name='product.template',
        string='Products',
        help='Keep empty for all products',
    )
    product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Products',
        help='Keep empty for all products',
    )
    show_standard_price = fields.Boolean(string='Show Cost Price')
    show_sale_price = fields.Boolean(string='Show Sale Price')
    show_vat_price = fields.Boolean(string='Show Sale Price with VAT')
    order_field = fields.Selection([
        ('name', 'Name'),
        ('default_code', 'Internal Reference'),
    ], string='Order')
    fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', string='Fiscal Position')
    qty1 = fields.Integer('Quantity-1', default=1)
    qty2 = fields.Integer('Quantity-2', default=5)
    qty3 = fields.Integer('Quantity-3', default=10)
    qty4 = fields.Integer('Quantity-4', default=0)
    qty5 = fields.Integer('Quantity-5', default=0)

    @api.model
    def default_get(self, fields):
        res = super(ProductPricelistPrint, self).default_get(fields)
        if self.env.context.get('active_model') == 'product.template':
            res['product_tmpl_ids'] = [
                (6, 0, self.env.context.get('active_ids', []))]
        elif self.env.context.get('active_model') == 'product.product':
            res['show_variants'] = True
            res['product_ids'] = [
                (6, 0, self.env.context.get('active_ids', []))]
        elif self.env.context.get('active_model') == 'product.pricelist':
            res['pricelist_id'] = self.env.context.get('active_id', False)
        elif self.env.context.get('active_model') == 'res.partner':
            res['partner_id'] = self.env.context.get('active_id', False)
            partner = self.env['res.partner'].browse(
                self.env.context.get('active_id', False))
            res['pricelist_id'] = partner.property_product_pricelist.id
        return res

    @api.one
    def get_attribute_price(self, product):
        attributes = self.env["product.attribute.value"].search([('product_ids.product_tmpl_id', '=', product.id)])
        variants = False
        for attr in attributes:
            #_logger.info("PRICE %s" % "-".join(["%s" % x.price_extra for x in attr.price_ids]))
            if attr.with_context(active_id=product.id).price_extra != 0.0:
                for value in attr.attribute_id.value_ids:
                    if not variants:
                        variants = value
                    else:
                        variants |= value
                break
        _logger.info("ATTR %s:%s" % (attributes, variants))
        return variants

    @api.one
    def get_variant_attribute(self, attribute, product):
        variants = False
        if attribute.product_ids:
            for product in product.product_variant_ids:
                if attribute.id in product.attribute_value_ids.ids:
                    if not variants:
                        variants = product
                        break
                    else:
                        variants |= product
        return variants

    @api.one
    def get_price_vat(self, product, price, qty):
        if self.fiscal_position_id and self.pricelist_id:
            company_id = self.env['res.company']._company_default_get('product.pricelist.print')
            fpos = self.fiscal_position_id or self.partner_id.property_account_position_id
            taxes = product.taxes_id.filtered(lambda r: not company_id or r.company_id == company_id)
            tax_id = fpos.map_tax(taxes, product, self.partner_id) if fpos else taxes
            return tax_id.compute_all(price, self.pricelist_id.currency_id, qty, product=product, partner=self.partner_id)['total_included']
        return [price]

    @api.one
    def get_price_currency(self, base_price):
        company_id = self.env['res.company']._company_default_get('product.pricelist.print')
        if self.pricelist_id and self.pricelist_id.currency_id != company_id.currency_id:
            product_context = dict(self.env.context, partner_id=self.partner_id.id, date=fields.Date.today())
            return self.env['res.currency'].browse(self.pricelist_id.currency_id).with_context(product_context).compute(base_price, self.order_id.pricelist_id.currency_id)
        return base_price

    @api.one
    def get_variants_as_table(self, product, field="default_code"):
        pivot = {}
        index = []
        names = ['price', 'row']
        max = 0
        prices = self.get_attribute_price(product)
        for atribute in product.attribute_line_ids.sorted(lambda r: r.attribute_id.sequence):
            if len(index) > 3:
                break
            pivot[atribute.name] = atribute.value_ids.ids
            max = max(max, len(atribute.value_ids.ids))
            if prices:
                for line in prices:
                    if atribute.id == line.id:
                        variant = self.get_variant_attribute(line, product)
                        index.append((variant.price, atribute.sequence))
            else:
                index.append(atribute.sequence)
        attr = np.empty((len(max)))
        attr[:] = np.nan
        for v,k in pivot.items():
            value = []
            for x in v:
                attribute = self.env['product.attribute.value'].browse(x)
                value.append(getattr(attribute, field))
            pivot[k] = value
            pivot[k] = np.concatenate((v, attr), axis=0)

    @api.multi
    def print_report(self):
        if not(self.pricelist_id or self.show_standard_price or
               self.show_sale_price):
            raise ValidationError(_(
                'You must set price list or any show price option.'))
        return self.env.ref(
            'product_pricelist_direct_print_vat.'
            'action_report_product_pricelist').report_action(self)

    @api.multi
    def action_pricelist_send(self):
        self.ensure_one()
        template_id = self.env.ref(
            'product_pricelist_direct_print_vat.email_template_edi_pricelist').id
        compose_form_id = self.env.ref(
            'mail.email_compose_message_wizard_form').id
        ctx = {
            'default_composition_mode': 'comment',
            'default_res_id': self.id,
            'default_model': 'product.pricelist.print',
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'partner_to': self.partner_id,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def force_pricelist_send(self):
        if self.env.context.get('active_model') != 'res.partner':
            return False
        template_id = self.env.ref(
            'product_pricelist_direct_print_vat.email_template_edi_pricelist').id
        composer = self.env['mail.compose.message'].with_context({
            'default_composition_mode': 'mass_mail',
            'default_notify': True,
            'default_res_id': self.id,
            'default_model': 'product.pricelist.print',
            'default_template_id': template_id,
            'active_ids': self.ids,
            'partner_to': self.partner_id,
        }).create({})
        values = composer.onchange_template_id(
            template_id, 'mass_mail', 'product.pricelist.print',
            self.id)['value']
        composer.write(values)
        composer.send_mail()
