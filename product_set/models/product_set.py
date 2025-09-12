# Copyright 2023 BioPrint Ltd.
# Copyright 2015 Anybox S.A.S
# Copyright 2016-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import fields, models, tools, api, _, Command, SUPERUSER_ID

_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _name = "product.set"
    _description = "Product set"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    @tools.ormcache()
    def _get_default_category_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('product.product_category_all')

    def _read_group_categ_id(self, categories, domain, order):
        category_ids = self.env.context.get('default_categ_id')
        if not category_ids and self.env.context.get('group_expand'):
            category_ids = categories._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return categories.browse(category_ids)

    name = fields.Char(help="Product set name", required=True, translate=True)
    display_name = fields.Char(help="Product set display name", compute="_compute_display_name")

    active = fields.Boolean(default=True)
    ref = fields.Char(
        string="Internal Reference", help="Product set internal reference", copy=False
    )
    set_line_ids = fields.One2many(
        "product.set.line", "product_set_id", string="Products", copy=True
    )
    set_pricelist_ids = fields.One2many(
        'product.set.pricelist',
        'product_set_id',
        string="Pricelists",
        copy=True,
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.company,
        ondelete="cascade",
        company_dependent=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        required=False,
        ondelete="cascade",
        company_dependent=True,
        index=True,
        help="You can attache the set to a specific partner "
             "or no one. If you don't specify one, "
             "it's going to be available for all of them.",
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Price list",
        # tracking=1,
        company_dependent=True,
        help="If you change the price list, only newly added lines will be affected.")
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        # compute='_compute_currency_id',
        # store=True,
        company_dependent=True,
        ondelete='restrict'
    )
    pricelist_amount_untaxed = fields.Monetary(
        string="Pricelist Untaxed Amount",
        related='set_pricelist_ids.amount_untaxed'
    )
    pricelist_count = fields.Integer(
        'Count price list',
        compute='_compute_count_pricelist_id'
    )
    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default=_get_default_category_id, group_expand='_read_group_categ_id',
        required=True
    )

    amount_untaxed = fields.Monetary(string="Untaxed Amount",
                                     store=True,
                                     compute='_compute_amounts',
                                     company_dependent=True,
                                     tracking=5
                                     )
    has_active_pricelist = fields.Boolean(
        compute='_compute_has_active_pricelist'
    )
    show_update_pricelist = fields.Boolean(
        string="Has Pricelist Changed"
    )  # True if the pricelist was changed
    price_list = fields.Selection(selection=[
        ('delete', _('Delete current price items')),
        ('add', _('Add current price items')),
        ('change', _('Change current price'))
    ],
        string="Price list Change",
        store=False,
        default="add",
    )

    @api.depends('pricelist_id', 'company_id')
    def _compute_count_pricelist_id(self):
        for record in self:
            count_price_list = self.env['product.pricelist.item'].search([
                ('product_set_id', '=', record.id),
            ]).mapped('pricelist_id')
            record.pricelist_count = len(count_price_list.ids)

    # @api.depends('pricelist_id', 'company_id')
    # def _compute_currency_id(self):
    #     for record in self:
    #         record.currency_id = record.pricelist_id.currency_id or record.company_id.currency_id
    #         for line in record.set_line_ids:
    #             line.currency_id = record.company_id.currency_id

    @api.depends('currency_id', 'company_id')
    def _compute_currency_rate(self):
        for record in self:
            record.currency_rate = self.env['res.currency']._get_conversion_rate(
                from_currency=record.company_id.currency_id,
                to_currency=record.currency_id,
                company=record.company_id,
                date=fields.Date.today(),
            )

    @api.depends('set_line_ids.price_subtotal')
    def _compute_amounts(self):
        for record in self:
            product_set_lines = record.set_line_ids.filtered(lambda x: not x.display_type)
            amount_untaxed = sum(product_set_lines.mapped('price_subtotal'))
            record.amount_untaxed = amount_untaxed
            pricelist_id = record.set_pricelist_ids.filtered(lambda r: r.pricelist_id.id == record.pricelist_id.id)
            if record.amount_untaxed > 0 and pricelist_id and pricelist_id.amount_untaxed == 0.0:
                pricelist_id.amount_untaxed = record.amount_untaxed

    @api.depends('company_id')
    def _compute_has_active_pricelist(self):
        for record in self:
            record.has_active_pricelist = bool(self.env['product.pricelist'].search(
                [('company_id', 'in', (False, record.company_id.id)), ('active', '=', True)],
                limit=1,
            ))

    @api.depends('name', 'ref')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{'[' + record.ref + '] ' if record.ref else ''}{record.name or ''}"

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id_show_update_prices(self):
        self.currency_id = self.pricelist_id.currency_id
        for line in self.set_line_ids:
            line.currency_id = self.pricelist_id.currency_id

        # _logger.info(f"Pricelist: {self.pricelist_id}-{self.set_pricelist_ids.filtered(lambda r: r.pricelist_id.id == self.pricelist_id.id)}")
        if not self.set_pricelist_ids.filtered(lambda r: r.pricelist_id.id == self.pricelist_id.id):
            pricelist_id = self.env['product.set.pricelist'].create({
                'pricelist_id': self.pricelist_id.id,
                'product_set_id': self.id,
                'company_id': self.company_id.id,
                'currency_id': self.pricelist_id.currency_id.id,
            })
            self.set_pricelist_ids |= pricelist_id
        self.show_update_pricelist = bool(self.set_line_ids)

    def _get_update_prices_lines(self):
        """ Hook to exclude specific lines which should not be updated based on price list recomputation """
        return self.set_line_ids.filtered(lambda line: not line.display_type)

    def action_update_prices(self):
        self.ensure_one()

        self._recompute_prices()

        if self.pricelist_id:
            message = _("Product prices have been recomputed according to pricelist %s.",
                        self.pricelist_id._get_html_link())
        else:
            message = _("Product prices have been recomputed.")
        self.message_post(body=message)

    def _compute_price_list(self):
        for record in self:
            if not record.pricelist_id:
                continue
            if record.set_pricelist_ids.filtered(lambda r: r.pricelist_id.id == record.pricelist_id.id):
                continue
            else:
                self.env['product.set.pricelist'].create({
                    'product_set_id': record.id,
                    'pricelist_id': record.pricelist_id.id,
                    'amount_untaxed': record.amount_untaxed,
                    'company_id': record.company_id.id,
                    'currency_id': record.currency_id.id,
                })

    def _recompute_prices(self):
        self._compute_price_list()
        lines_to_recompute = self._get_update_prices_lines()
        lines_to_recompute.invalidate_recordset(['pricelist_item_id'])
        lines_to_recompute._compute_price_list_item()
        self.show_update_pricelist = False

    def synchronize_prices(self):
        pricelist_ids = self.env['product.pricelist']
        for record in self:
            external_pricelist_item_ids = self.env['product.pricelist.item'].search([
                ('product_set_id', '=', record.id)
            ])
            for line in record.set_line_ids:
                if line.product_id:
                    by_product = external_pricelist_item_ids.filtered(lambda r: r.product_id.id == line.product_id.id)
                    if by_product:
                        pricelist_ids |= by_product.mapped('pricelist_id')
                        for pricelist_item_id in by_product.filtered(
                            lambda r: r.pricelist_id.id == record.pricelist_id.id):
                            line.pricelist_item_id = pricelist_item_id

                if line.product_tmpl_id:
                    by_template = external_pricelist_item_ids.filtered(
                        lambda r: r.product_tmpl_id.id == line.product_tmpl_id.id)
                    if by_template:
                        pricelist_ids |= by_template.mapped('pricelist_id')
                        for pricelist_item_id in by_template.filtered(
                            lambda r: r.pricelist_id.id == record.pricelist_id.id):
                            line.pricelist_item_id = pricelist_item_id

            for pricelist_id in pricelist_ids.filtered(
                lambda r: r.id not in record.set_pricelist_ids.mapped('pricelist_id').ids):
                record.set_pricelist_ids |= self.env['product.set.pricelist'].create({
                    'product_set_id': record.id,
                    'pricelist_id': pricelist_id.id,
                    'company_id': record.company_id.id,
                    'currency_id': record.currency_id.id,
                })

    def name_get(self):
        return [(rec.id, rec._name_get()) for rec in self]

    def _name_get(self):
        parts = []
        if self.ref:
            parts.append("[%s]" % self.ref)
        parts.append(self.name)
        if self.partner_id:
            parts.append("@ %s" % self.partner_id.name)
        return " ".join(parts)


    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        name_name = False
        if name:
            for single_domain in args:
                if isinstance(single_domain, (list, tuple)) and single_domain[0] == 'name':
                    name_name = True
                    domain += ['|', ('name', operator, name), ('ref', 'ilike', name)]
                elif isinstance(single_domain, (list, tuple)):
                    domain += [single_domain]
                else:
                    domain += single_domain
            if not name_name:
                domain = ['|', ['name', operator, name], ['ref', 'ilike', name]] + domain
            args = domain
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
