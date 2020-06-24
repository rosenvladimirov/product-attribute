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
    report_lines = fields.One2many('product.pricelist.print.line', 'report_id', string="Prices")

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
        #_logger.info("ATTR %s:%s" % (attributes, variants))
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

    def _get_field_value(self, product, partner, pricelist):
        price_extra = 0.0
        for attribute_price in product.mapped('attribute_value_ids.price_ids'):
            if attribute_price.product_tmpl_id == product.product_tmpl_id:
                price_extra += attribute_price.price_extra
        if price_extra == 0.0:
            return False
        return {
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_id': product.id,
                'partner_id': partner.id,
                'pricelist_id': pricelist.id,
                'quantity': self.quantity,
                'standard_price': product.standard_price,
                }

    def _get_key_value(self, partner_id, pricelist_id, product_tmpl_id, product_id):
        return '%s-%s-%s-%s' % (partner_id, pricelist_id, product_tmpl_id, product_id)

    @api.multi
    def analize_report(self):
        for rec in self:
            if rec.pricelist_id and not rec.pricelist_ids:
                rec.pricelist_ids = [(6, 0, [rec.pricelist_id.id])]
            if not(rec.pricelist_ids or rec.partner_count
                   or rec.show_standard_price or rec.show_sale_price):
                raise ValidationError(_(
                    'You must set price list or any customer '
                    'or any show price option.'))
            values = []
            ctx_products = self._context.get('ctx_products', False)
            products = rec.product_ids or ctx_products
            if not products:
                domain = ["|"]
                if rec.product_tmpl_ids:
                    domain += [('product_tmpl_id', 'in', rec.product_tmpl_ids.ids)]
                if rec.pricelist_ids:
                    product_ids = set([x.product_id.id for x in rec.pricelist_ids.mapped('item_ids') if x.product_id])
                    if product_ids:
                        domain += [('id', 'in', list(product_ids))]
                    product_ids = set([x.product_tmpl_id.id for x in rec.pricelist_ids.mapped('item_ids') if x.product_tmpl_id])
                    if product_ids:
                        domain += [('product_tmpl_id', 'in', list(product_ids))]
                products = rec.env['product.product'].search(domain)

            ctx_partners = self._context.get('ctx_partners', False)
            partners = rec.partner_ids or ctx_partners
            if not partners:
                if rec.pricelist_ids:
                    partners = rec.env['res.partner'].search([('property_product_pricelist', 'in', rec.pricelist_ids.ids)])
            filter_values = {}
            for product in products:
                for partner in partners:
                    for pricelist in rec.pricelist_ids:
                        product_ids = set([x.product_id.id for x in pricelist.mapped('item_ids') if x.product_id])
                        product_tmpl_ids = set([x.product_tmpl_id.id for x in pricelist.mapped('item_ids') if x.product_tmpl_id])
                        if partner.property_product_pricelist.id == pricelist.id and (product.id in list(product_ids) or product.product_tmpl_id.id in list(product_tmpl_ids)):
                            res = rec._get_field_value(product, partner, pricelist)
                            if res:
                                filter_values[rec._get_key_value(res['partner_id'], res['pricelist_id'], res['product_tmpl_id'], res['product_id'])] = (0, False, res)
            for curr in filter_values.items():
                values.append(curr)
            rec.update({'report_lines': values})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Product prices'),
            'view_type': 'form',
            'view_mode': 'tree,graph,pivot',
            'res_model': 'product.pricelist.print.line',
            #'view_id': self.env.ref('product_pricelist_direct_print.view_product_pricelist_print_line_tree').id,
            'search_view_id': self.env.ref('product_pricelist_direct_print.view_product_pricelist_print_line_filter').id,
            'target': 'main',
            'domain': [('report_id', '=', self.id)],
            'context': {'order_field': self.order_field, 'show_standard_price': self.show_standard_price},
        }

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


class ProductPricelistPrintLine(models.TransientModel):
    _name = 'product.pricelist.print.line'
    _description = 'Product pricelist print line'
    _rec_name = 'product_id'
    _order = 'default_code,name'

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            fpos = line.set_id.fiscal_position_id or line.set_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.partner_id) if fpos else taxes

    report_id = fields.Many2one('product.pricelist.print', string='Product Report Print', ondelete="cascade")
    product_tmpl_id = fields.Many2one(comodel_name='product.template', string='Product template', readonly=True, group_operator='avg')
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    default_code = fields.Char(related='product_id.default_code', string='Product ref', store=True)
    name = fields.Char(related='product_id.name', string='Product name', store=True)

    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    product_uom = fields.Many2one('product.uom', related="product_id.uom_id", string='Unit of Measure', readonly=True)
    standard_price = fields.Float('Cost', digits=dp.get_precision('Product Price'), groups="base.group_user",
        help="Cost used for stock valuation in standard price and as a first price to set in average/fifo. "
             "Also used as a base price for pricelists. "
             "Expressed in the default unit of measure of the product.")
    price_unit = fields.Monetary(compute='_compute_price_unit', string='Unit price', readonly=True, store=True)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    #product_set_id = fields.Many2one('product.set', string='Product Set', ondelete="restrict")
    company_id = fields.Many2one(related='report_id.company_id', string='Company')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', compute_sudo=True, help="Pricelist for current sales order.")
    currency_id = fields.Many2one(related='pricelist_id.currency_id', string='Currency', store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])

    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer')

    @api.depends('report_id', 'tax_id', 'company_id', 'product_id')
    def _compute_price_unit(self):
        for line in self:
            _logger.info("COMPUTE PRICE %s:%s:%s" % (line.product_id, line.pricelist_id, line.partner_id))
            if line.product_id and line.pricelist_id and line.partner_id:
                line.update({'price_unit':
                              self.env['account.tax']._fix_tax_included_price_company(line._get_display_price(line.product_id), line.product_id.taxes_id, line.tax_id, line.company_id)})
            else:
                line.update({'price_unit': 0.0})

    @api.depends('quantity', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit
            taxes = line.tax_id.compute_all(price, line.pricelist_id.currency_id, line.quantity, product=line.product_id, partner=line.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _get_display_price_context(self):
        #, product_set_id=self.product_set_id.id
        return dict(self.env.context, partner_id=self.partner_id.id, date=fields.Date.context_today(self),
                                uom=self.product_uom.id, company_id=self.pricelist_id.company_id.id)

    @api.multi
    def _get_display_price(self, product):
        PricelistItem = self.env['product.pricelist.item'].sudo()
        product_context = self._get_display_price_context()
        final_price, rule_id = self.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.quantity or 1.0, self.partner_id)
        base_price, currency_id = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.quantity or 1.0, self.product_uom, self.pricelist_id.id)
        if currency_id != self.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(product_context).compute(base_price, self.pricelist_id.currency_id)
        if rule_id and PricelistItem.browse(rule_id).compute_price == 'fixed':
            return final_price
        elif rule_id and PricelistItem.browse(rule_id).price_discount >= 0.0:
            return min(base_price, final_price)
        else:
            return max(base_price, final_price)

    def _get_real_price_currency_context(self, uom):
        #, product_set_id=self.product_set_id
        return dict(uom=uom.id)

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        PricelistItem = self.env['product.pricelist.item'].sudo()
        field_name = 'lst_price'
        currency_id = None
        product_currency = None
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            product_context = self._get_real_price_currency_context(uom)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(product_context).get_product_price_rule(product, qty, self.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
            if pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        product_currency = product_currency or(product.company_id and product.company_id.currency_id) or self.env.user.company_id.currency_id
        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id)

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0
        #_logger.info("PRICELIST GET CURRENCY RODUCT:%s:CURRENCY:%s:%s:%s:%s" % (product_currency.name, product.company_id.name, currency_id.name, self.env.user.company_id.name, self.env.user.company_id.currency_id.name))
        return product[field_name] * uom_factor * cur_factor, currency_id.id

    @api.multi
    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.product_id = rec.product_tmpl_id.product_variant_id.id
                self._compute_tax_id()
                self._compute_price_unit()
                return {'domain': {'product_id': [('product_tmpl_id', '=', rec.product_tmpl_id.id)]}}
