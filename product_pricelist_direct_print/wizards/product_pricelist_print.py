# Copyright 2017 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
    hide_pricelist_name = fields.Boolean(string='Hide Pricelist Name')

    multipricelist = fields.Boolean(string='Use Multi Pricelists')
    only_product_pricelist = fields.Boolean(string='Show Products with used Pricelist')

    order_field = fields.Selection([
        ('name', 'Name'),
        ('default_code', 'Internal Reference'),
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
        elif self.env.context.get('active_model') == 'product.pricelist.item':
            active_ids = self.env.context.get('active_ids', [])
            items = self.env['product.pricelist.item'].browse(active_ids)
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

    def _get_field_value(self, product, partner, pricelist):
        return {
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_id': product.id,
                'quantity': self.quantity,
                'standard_price': product.standard_price,
                'partner_id': partner.id,
                'pricelist_id': pricelist.id,
                }

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
                    partners = rec.env['res.partner'].search([]).filtered(lambda x: x.property_product_pricelist.id in rec.pricelist_ids.ids)

            for product in products:
                for partner in partners:
                    for pricelist in rec.pricelist_ids:
                        product_ids = set([x.product_id.id for x in pricelist.mapped('item_ids') if x.product_id])
                        product_tmpl_ids = set([x.product_tmpl_id.id for x in pricelist.mapped('item_ids') if x.product_tmpl_id])
                        if partner.property_product_pricelist.id == pricelist.id and (product.id in list(product_ids) or product.product_tmpl_id.id in list(product_tmpl_ids)):
                            values.append((0, False, rec._get_field_value(product, partner, pricelist)))
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
