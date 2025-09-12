# Copyright 2023 BioPrint Ltd.
# Copyright 2015 Anybox S.A.S
# Copyright 2016-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import fields, models, api, _, Command

_logger = logging.getLogger(__name__)


class ProductSetLine(models.Model):
    _name = "product.set.line"
    _description = "Product set line"
    _rec_name = "product_id"
    _order = "product_set_id, sequence, product_id"

    display_type = fields.Selection(
        [
            ("line_section", "Section"),
            ("line_note", "Note"),
        ]
    )
    applied_on = fields.Selection(
        selection=[
            ('3_global', "All Products"),
            ('1_product', "Product"),
            ('0_product_variant', "Product Variant"),
        ],
        string="Price list Apply On",
        default='3_global',
        help="Pricelist Item applicable on selected option")

    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        domain=[("sale_ok", "=", True)],
        string="Product Template",
        required=False,
    )
    product_choice = fields.Binary(
        compute='_compute_product_choice',
        string='Technical domain Product Choice'
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        domain=[("sale_ok", "=", True)],
        string="Product",
        required=False,
    )

    quantity = fields.Float(
        digits="Product Unit of Measure", required=True, default=1.0
    )
    fixed_price = fields.Float(
        string="Fixed Price in set",
        digits='Product Price',
        related='pricelist_item_id.fixed_price',
    )
    compute_price = fields.Selection(
        string="Price base on",
        related='pricelist_item_id.compute_price'
    )
    product_set_id = fields.Many2one(
        "product.set",
        string="Set",
        ondelete="cascade",
        index=True,
        required=True,
    )

    active = fields.Boolean(
        string="Active",
        related="product_set_id.active",
        store=True,
        readonly=True
    )
    sequence = fields.Integer(required=True, default=0)
    # company_id = fields.Many2one(
    #     "res.company", related="product_set_id.company_id", store=True, readonly=True
    # )
    currency_id = fields.Many2one(
        related='product_set_id.currency_id',
        depends=['product_set_id.currency_id'],
        company_dependent=True,
        store=True,
        precompute=True)

    name = fields.Char()
    price_subtotal = fields.Monetary(
        string="Subtotal",
        compute='_compute_amount',
        company_dependent=True,
        store=True,
        precompute=True)
    pricelist_item_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        string='Product Price item',
    )
    show_update_pricelist = fields.Boolean(
        string="Has Pricelist Changed")

    @api.depends('quantity', 'fixed_price')
    def _compute_amount(self):
        for line in self:
            amount_untaxed = line.quantity * line.fixed_price
            if line.pricelist_item_id and line.fixed_price != line.pricelist_item_id.fixed_price:
                line.pricelist_item_id.fixed_price = line.fixed_price
            _logger.info(f'Price line: {line.pricelist_item_id}={line.fixed_price}')
            line.update({
                'price_subtotal': amount_untaxed,
            })

    @api.depends('product_id', 'product_tmpl_id')
    def _compute_product_choice(self):
        for record in self:
            if record.product_tmpl_id:
                record.product_choice = [('product_tmpl_id', '=', record.product_tmpl_id.id)]
            else:
                record.product_choice = []

    @api.onchange('product_tmpl_id')
    @api.depends('pricelist_item_id', 'applied_on')
    def _onchange_product_tmpl_id(self):
        for record in self:
            if record.product_tmpl_id and record.product_id \
                    and (record.product_id.product_tmpl_id.id != record.product_tmpl_id.id):
                record.product_id = record.product_tmpl_id.product_variant_id
            if record.product_tmpl_id and record.pricelist_item_id and record.applied_on == '1_product':
                record.pricelist_item_id.product_tmpl_id = record.product_tmpl_id.id
                record.pricelist_item_id.product_id = False

    @api.onchange('product_id')
    @api.depends('pricelist_item_id', 'applied_on')
    def _onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.product_tmpl_id = record.product_id.product_tmpl_id
            if record.product_id and record.pricelist_item_id and record.applied_on == '0_product_variant':
                record.pricelist_item_id.product_id = record.product_id.id

    @api.depends('product_id', 'quantity')
    def _compute_price_list_item(self):
        for record in self:
            if record.product_set_id.price_list == 'add':
                pricelist_item_id = False
                product_pricelist_item_id = self.env['product.pricelist.item'].search([
                    ('product_id', '=', record.product_id.id),
                    ('pricelist_id', '=', record.product_set_id.pricelist_id.id),
                    ('product_set_id', '=', record.product_set_id.id),
                ], limit=1)
                template_pricelist_item_id = self.env['product.pricelist.item'].search([
                    ('product_tmpl_id', '=', record.product_tmpl_id.id),
                    ('pricelist_id', '=', record.product_set_id.pricelist_id.id),
                    ('product_set_id', '=', record.product_set_id.id),
                ], limit=1)

                applied_on = record.product_tmpl_id and '1_product' or record.applied_on
                if record.product_id:
                    applied_on = '0_product_variant'

                if product_pricelist_item_id and product_pricelist_item_id != record.pricelist_item_id:
                    pricelist_item_id = product_pricelist_item_id
                    applied_on = pricelist_item_id.applied_on
                elif template_pricelist_item_id and template_pricelist_item_id != record.pricelist_item_id:
                    pricelist_item_id = template_pricelist_item_id
                    applied_on = pricelist_item_id.applied_on

                if not pricelist_item_id:
                    pricelist_item_id = self.env['product.pricelist.item'].create({
                        'applied_on': applied_on,
                        'product_set_id': record.product_set_id.id,
                        'pricelist_id': record.product_set_id.pricelist_id.id,
                        'product_id': record.product_id.id,
                        'product_tmpl_id': record.product_tmpl_id.id,
                        'compute_price': 'fixed',
                        'product_set_line_id': record.id,
                    })

                record.pricelist_item_id = pricelist_item_id
                record.applied_on = applied_on if pricelist_item_id.applied_on == applied_on else pricelist_item_id.applied_on
                record.show_update_pricelist = True

            if record.product_set_id.price_list == 'delete' \
                    and record.pricelist_item_id.pricelist_id.id != record.pricelist_item_id.pricelist_id.id:
                record.pricelist_item_id.unlink()
                record.show_update_pricelist = False
                record._compute_price_list_item()

    def _get_compensation_product_id(self, vals):
        values = {}
        compensation_product_id = self.with_company(self.env.company).env.ref('product_set.compensation_product',
                                                                              raise_if_not_found=False)
        if compensation_product_id and vals.get("product_set_id"):
            product_set_id = self.env["product.set"].browse(vals["product_set_id"])
            if not product_set_id.set_line_ids.filtered(lambda r: r.product_id.id == compensation_product_id.id):
                values.update({
                    "product_id": compensation_product_id.id,
                    "product_tmpl_id": compensation_product_id.product_tmpl_id.id,
                    "product_set_id": self.product_set_id.id,
                    "sequence": 0,
                })
        return values

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("product_set_id"):
                product_set_id = self.env["product.set"].browse(vals["product_set_id"])
                if product_set_id and len(product_set_id.set_line_ids) > 0:
                    vals['sequence'] = product_set_id.set_line_ids[-1].sequence + 1
        res = super().create(vals_list)
        for record, vals in zip(res, vals_list):
            values = record._get_compensation_product_id(vals)
            if values:
                record.product_set_id.set_line_ids |= self.env['product.set.line'].create(values)
        return res

    def write(self, vals):
        # _logger.info('VALS %s' % vals)
        compensation_product_id = self.with_company(self.env.company).env.ref(
            'product_set.compensation_product',
            raise_if_not_found=False).id

        res = super(ProductSetLine, self).write(vals)
        if vals.get("fixed_price"):
            for line in self:
                total_price = sum(line.product_set_id.mapped('set_pricelist_ids').filtered(
                    lambda r: r.pricelist_id.id == line.product_set_id.pricelist_id.id).mapped('amount_untaxed'))
                rest_price = sum(line.product_set_id.mapped('set_line_ids').
                                 filtered(lambda r: r.product_id.id != compensation_product_id).mapped('fixed_price'))
                rest_fixed_price = total_price - rest_price
                rest_product_id = line.product_set_id.mapped('set_line_ids'). \
                    filtered(lambda r: r.product_id.id == compensation_product_id)
                _logger.info(f'{compensation_product_id}:{rest_product_id}:{line.fixed_price}<>{rest_fixed_price}')
                if rest_product_id:
                    rest_product_id.pricelist_item_id.fixed_price = rest_fixed_price
        return res
