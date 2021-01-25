# Copyright 2017 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - David Vidal
# Copyright 2019 dXFactory - Rosen Vladimirov
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from itertools import groupby

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductPricelistPrint(models.TransientModel):
    _name = 'product.pricelist.print'

    base_on = fields.Selection([
        ('pricelist', 'Price list name'),
    ], string='Base on', default='pricelist')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('product.pricelist.print'))
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
    )
    pricelist_ids = fields.Many2many(
        comodel_name='product.pricelist',
        string='Pricelists',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Customers',
    )
    categ_ids = fields.Many2many(
        comodel_name='product.category',
        string='Categories',
    )
    product_from_pricelist = fields.Boolean()
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
    show_sale_wh_vat_price = fields.Boolean(string='Show Sale Price without VAT')
    hide_pricelist_name = fields.Boolean(string='Hide Pricelist Name')
    display_pictures = fields.Boolean(string='Show Product pictures')
    image_sizes = fields.Selection(
        [('image', 'Big sized Image'), ('image_medium', 'Medium Sized Image'),
         ('image_small', 'Small Sized Image')],
        'Image Sizes', default="image_small",
        help="Image size to be displayed in report")

    multipricelist = fields.Boolean(string='Use Multi Pricelists')
    only_product_pricelist = fields.Boolean(string='Show Products with used Pricelist')

    order_field = fields.Selection([
        ('name', 'Name'),
        ('default_code', 'Internal Reference'),
        ('code', 'Price list code'),
    ], string='Order')
    partner_count = fields.Integer(
        compute='_compute_partner_count'
    )
    date = fields.Date()
    last_ordered_products = fields.Integer(
        help="If you enter an X number here, then, for each selected customer,"
             " the last X ordered products will be obtained for the report."
    )
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1)

    report_lines = fields.One2many('product.pricelist.print.line', 'report_id', string="Prices")

    @api.multi
    @api.depends('partner_ids')
    def _compute_partner_count(self):
        for record in self:
            self.partner_count = len(record.partner_ids)

    @api.onchange('partner_ids')
    def _onchange_partner_ids(self):
        if not self.partner_count:
            self.last_ordered_products = False

    @api.onchange('product_from_pricelist', 'pricelist_id')
    def _onchange_product_from_pricelist(self):
        if self.pricelist_id and self.product_from_pricelist:
            res = self.with_context(from_pricelist_id=self.pricelist_id.item_ids.ids).default_get([])
            if res.get('product_ids'):
                self.product_ids = res['product_ids']
                self.show_variants = True
                if self.order_field == 'name':
                    self.product_ids = self.product_ids.sorted(lambda x: x.name)
                elif self.order_field == 'default_code':
                    self.product_ids = self.product_ids.sorted(lambda x: x.default_code or '')
            if res.get('product_tmpl_ids'):
                self.product_tmpl_ids = res['product_tmpl_ids']
            if res.get('categ_ids'):
                self.categ_ids = res['categ_ids']
        if not self.product_from_pricelist:
            self.partner_id = False

    @api.onchange('order_field')
    def _onchange_order_field(self):
        if self.order_field == 'name':
            self.product_ids.sorted(lambda x: x.name)
        elif self.order_field == 'default_code':
            self.product_ids.sorted(lambda x: x.default_code or '')

    @api.model
    def default_get(self, fields):
        active_ids = self._context.get('active_ids') and self._context['active_ids'] or self._context.get('active_id') and [self._context['active_id']] or self.id
        res = super(ProductPricelistPrint, self).default_get(fields)
        if self.env.context.get('active_model') == 'product.template':
            res['product_tmpl_ids'] = [
                (6, 0, self.env.context.get('active_ids', []))]
        elif self.env.context.get('active_model') == 'product.product':
            res['show_variants'] = True
            res['product_ids'] = [
                (6, 0, self.env.context.get('active_ids', []))]
        elif self.env.context.get('active_model') == 'product.pricelist':
            if len(active_ids) == 1:
                res['pricelist_id'] = self.env.context.get('active_id', False)
            else:
                res['pricelist_ids'] = [(6, 0, active_ids)]
        elif self.env.context.get('active_model') == 'res.partner':
            active_ids = self.env.context.get('active_ids', [])
            res['partner_ids'] = [(6, 0, active_ids)]
            if len(active_ids) == 1:
                partner = self.env['res.partner'].browse(active_ids[0])
                res['pricelist_id'] = partner.property_product_pricelist.id
        elif self.env.context.get('active_model') == 'product.pricelist.item' or self.env.context.get('from_pricelist_id'):
            active_ids = self.env.context.get('from_pricelist_id') or self.env.context.get('active_ids', [])
            items = self.env['product.pricelist.item'].browse(active_ids)
            #_logger.info("GET Items %s" % (items))
            if not items:
                return {}
            # Set pricelist if all the items belong to the same one
            if len(items.mapped('pricelist_id')) == 1:
                res['pricelist_id'] = items[0].pricelist_id.id
            product_items = items.filtered(
                lambda x: x.applied_on == '0_product_variant')
            template_items = items.filtered(
                lambda x: x.applied_on == '1_product')
            category_items = items.filtered(
                lambda x: x.applied_on == '2_product_category')
            # Convert al pricelist items to their affected variants
            if product_items:
                res['show_variants'] = True
                product_ids = product_items.mapped('product_id')
                product_ids |= template_items.mapped(
                    'product_tmpl_id.product_variant_ids')
                product_ids |= product_ids.search([
                    ('sale_ok', '=', True),
                    ('categ_id', 'in', category_items.mapped('categ_id').ids)
                ])
                res['product_ids'] = [(6, 0, product_ids.ids)]
            # Convert al pricelist items to their affected templates
            if template_items and not product_items:
                product_tmpl_ids = template_items.mapped('product_tmpl_id')
                product_tmpl_ids |= product_tmpl_ids.search([
                    ('sale_ok', '=', True),
                    ('categ_id', 'in', category_items.mapped('categ_id').ids)
                ])
                res['product_tmpl_ids'] = [
                    (6, 0, product_tmpl_ids.ids)]
            # Only category items, we just set the categories
            if category_items and not product_items and not template_items:
                res['categ_ids'] = [
                    (6, 0, category_items.mapped('categ_id').ids)]
        return res

    def _get_field_value(self, product, partner, pricelist, page):
        #price_extra = 0.0
        #for attribute_price in product.mapped('attribute_value_ids.price_ids'):
        #    if attribute_price.product_tmpl_id == product.product_tmpl_id:
        #        price_extra += attribute_price.price_extra
        #if price_extra == 0.0:
        #    return False
        price, vat, price_vat, price_wh_vat = self.get_price(product, pricelist=pricelist)[0]
        if not price:
            return False
        return {
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_id': product.id,
                'partner_id': partner.id,
                'pricelist_id': pricelist.id,
                'currency_id': pricelist.currency_id.id,
                'quantity': self.quantity,
                'standard_price': product.standard_price,
                'price_unit': price,
                'price_tax': vat,
                'price_subtotal': price_wh_vat,
                'price_total': price_vat,
                'company_id': self.env.user.company_id.id,
                'report_id': self.id,
                }

    def _get_key_value(self, partner_id, pricelist_id, product_tmpl_id, product_id, page):
        return '%s-%s-%s-%s' % (partner_id, pricelist_id, product_tmpl_id, product_id)

    def _get_product_layouted(self, products, pricelist, date):
        return self.product_layouted(products, pricelist, date)

    @api.multi
    def analize_report(self):
        for rec in self:
            #if rec.pricelist_id and not rec.pricelist_ids:
            #    rec.pricelist_ids = [(6, 0, [rec.pricelist_id.id])]
            #if not(rec.pricelist_id or rec.partner_count
            #       or rec.show_standard_price or rec.show_sale_price):
            #    raise ValidationError(_(
            #        'You must set price list or any customer '
            #        'or any show price option.'))
            values = []
            pricelist = rec.get_pricelist_to_print()
            products = rec.product_ids
            #ctx_products = self._context.get('ctx_products', False)
            #products = rec.product_ids or ctx_products
            products = rec._get_product_layouted(products, pricelist, rec.date)
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

            #ctx_partners = self._context.get('ctx_partners', False)
            #partners = rec.partner_ids or ctx_partners
            if rec.pricelist_id:
                partners = rec.env['res.partner'].search([('property_product_pricelist', '=', rec.pricelist_id.id)])
            filter_values = {}
            #_logger.info("DATA %s:%s:%s" % (partners, pricelist, products))
            for partner in partners:
                for page in products:
                    for product_add in page:
                        #_logger.info("PAGE %s" % product_add)
                        if product_add.get('single_product'):
                            for product in product_add['lines']:
                                res = rec._get_field_value(product, partner, pricelist, product_add)
                                #_logger.info("LINE 1 %s:%s:%s:::%s" % (product, partner, pricelist, res))
                                if res:
                                    filter_values[rec._get_key_value(res['partner_id'], res['pricelist_id'], res['product_tmpl_id'], res['product_id'], product_add)] = (0, False, res)
                        else:
                            if product_add.get('has_variant_with_price'):
                                for product in product_add['lines']:
                                    res = rec._get_field_value(product, partner, pricelist, product_add)
                                    #_logger.info("LINE 2 %s:%s:%s:::%s" % (product, partner, pricelist, res))
                                    if res:
                                        filter_values[rec._get_key_value(res['partner_id'], res['pricelist_id'], res['product_tmpl_id'], res['product_id'], product_add)] = (0, False, res)
                            elif len(product_add['lines']) > 0:
                                product = product_add['lines'][0]
                                res = rec._get_field_value(product, partner, pricelist, product_add)
                                #_logger.info("LINE 3 %s:%s:%s:::%s" % (product, partner, pricelist, res))
                                if res:
                                    filter_values[rec._get_key_value(res['partner_id'], res['pricelist_id'], res['product_tmpl_id'], res['product_id'], product_add)] = (0, False, res)
            for curr in filter_values.values():
                values.append(curr)
                _logger.info("VALUES %s" % curr[2])
                rec.report_lines = curr
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

    @api.one
    def get_price(self, product, pricelist=False, date=False, qty=1.0):
        fpos = self.partner_id and self.partner_id.property_account_position_id or self.env.user.company_id.partner_id.property_account_position_id
        line_company_id = self.env.user.company_id
        taxes = product.taxes_id.filtered(lambda r: not line_company_id or r.company_id == line_company_id)
        tax_id = fpos.map_tax(taxes, product, self.partner_id) if fpos else taxes
        unit_price = product.with_context(pricelist=pricelist and pricelist.id,
                                 date=date,
                                 quantity=qty,
                                 partner_id=self.partner_id and self.partner_id.id).price
        price = self.env['account.tax']._fix_tax_included_price_company(unit_price, product.taxes_id, tax_id, line_company_id)
        taxes = tax_id.compute_all(price, pricelist.currency_id, qty)
        return (price > 0.0, sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])), taxes['total_included'], taxes['total_excluded'])

    @api.multi
    def product_layouted(self, product, pricelist, date):
        self.ensure_one()
        report_pages = [[]]
        for category, lines in groupby(product, lambda l: l.product_tmpl_id):
            # Append category to current report page
            #_logger.info("CATEGORY %s" % category)
            codes = set()
            for line in list(lines):
                if line.with_context(dict(self._context, pricelist=pricelist.id)).pricelist_code:
                    codes.update([line.with_context(dict(self._context, pricelist=pricelist.id)).pricelist_code])
            report_pages[-1].append({
                'name': category and category.display_name or _('Uncategorized'),
                'lines': list(lines),
                'has_variant_with_price': category.product_variant_count > 1 and category.check_for_price(pricelist, date),
                'single_product': category.product_variant_count == 1,
                'codes': codes and list(codes) or False,
            })
            #_logger.info("PAGE %s:%s" % (category.display_name, category.product_variant_count > 1 and category.check_for_price(pricelist, date)))
        return report_pages

    @api.multi
    def print_report(self):
        if not(self.pricelist_id or self.partner_count
               or self.show_standard_price or self.show_sale_price):
            raise ValidationError(_(
                'You must set price list or any customer '
                'or any show price option.'))
        return self.env.ref(
            'product_pricelist_direct_print.'
            'action_report_product_pricelist').report_action(self)

    @api.multi
    def action_pricelist_send(self):
        self.ensure_one()
        if self.partner_count > 1:
            self.send_batch()
        else:
            if self.partner_count == 1:
                partner = self.partner_ids[0]
                self.write({
                    'partner_id': partner.id,
                    'pricelist_id': partner.property_product_pricelist.id,
                })
            return self.message_composer_action()

    @api.multi
    def message_composer_action(self):
        self.ensure_one()

        template_id = self.env.ref(
            'product_pricelist_direct_print.email_template_edi_pricelist').id
        compose_form_id = self.env.ref(
            'mail.email_compose_message_wizard_form').id
        ctx = {
            'default_composition_mode': 'comment',
            'default_res_id': self.id,
            'default_model': 'product.pricelist.print',
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
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
    def send_batch(self):
        self.ensure_one()
        for partner in self.partner_ids.filtered(lambda x: not x.parent_id):
            self.write({
                'partner_id': partner.id,
                'pricelist_id': partner.property_product_pricelist.id,
            })
            self.force_pricelist_send()

    @api.multi
    def force_pricelist_send(self):
        template_id = self.env.ref(
            'product_pricelist_direct_print.email_template_edi_pricelist').id
        composer = self.env['mail.compose.message'].with_context({
            'default_composition_mode': 'mass_mail',
            'default_notify': True,
            'default_res_id': self.id,
            'default_model': 'product.pricelist.print',
            'default_template_id': template_id,
            'active_ids': self.ids,
        }).create({})
        values = composer.onchange_template_id(
            template_id, 'mass_mail', 'product.pricelist.print',
            self.id)['value']
        composer.write(values)
        composer.send_mail()

    @api.multi
    def get_last_ordered_products_to_print(self):
        self.ensure_one()
        partner = self.partner_id
        if not partner and self.partner_count == 1:
            partner = self.partner_ids[0]
        orders = partner.sale_order_ids.filtered(
            lambda r: r.state not in ['draft', 'sent', 'cancel'])
        orders = orders.sorted(key=lambda r: r.confirmation_date, reverse=True)
        products = orders.mapped('order_line').mapped('product_id')
        return products[:self.last_ordered_products]

    @api.multi
    def get_pricelist_to_print(self):
        self.ensure_one()
        pricelist = self.pricelist_id
        if not pricelist and self.partner_count == 1:
            pricelist = self.partner_ids[0].property_product_pricelist
        return pricelist


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
    price_unit = fields.Float(string='Unit price', digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Float(string='Subtotal')
    price_tax = fields.Float(string='Taxes')
    price_total = fields.Float(string='Total')

    #product_set_id = fields.Many2one('product.set', string='Product Set', ondelete="restrict")
    company_id = fields.Many2one(related='report_id.company_id', string='Company')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', compute_sudo=True, help="Pricelist for current sales order.")
    currency_id = fields.Many2one('res.currency', string='Currency')
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])

    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer')
