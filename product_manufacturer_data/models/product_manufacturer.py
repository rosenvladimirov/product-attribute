# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ProductManufacturer(models.Model):
    _name = "product.manufacturer"
    _description = "Information about a product manufacturer"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _rec_name = 'display_name'

    active = fields.Boolean(
        'Active',
        default=True,
        help="If the active field is set to False, it will allow you to hide the bills of material without removing it."
    )
    sequence = fields.Integer(
        index=True,
        default=1
    )
    manufacturer = fields.Many2one(
        comodel_name='res.partner',
        string='Manufacturer',
        required=True,
    )
    manufacturer_pname = fields.Char(string='Manuf. Product Name')
    manufacturer_pref = fields.Char(string='Manuf. Product Code')
    manufacturer_purl = fields.Char(string='Manuf. Product URL')
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company.id,
        index=1
    )

    product_tmpl_id = fields.Many2one(
        'product.template',
        'Product Template',
        ondelete='cascade',
        required=True,
        index=1,
        help="Specify a template if this rule only applies to one product template. Keep empty otherwise."
    )
    product_id = fields.Many2one(
        'product.product',
        'Product variant',
        ondelete='cascade',
        index=1,
        help="Specify a product if this rule only applies to one product. Keep empty otherwise."
    )
    product_variant_id = fields.Many2one(
        'product.product',
        compute='_compute_product_variant_id',
        string='Product Variant',
    )

    supplierinfo_ids = fields.One2many(
        'product.supplierinfo',
        'manufacturer_id',
        'Supplier Information',
    )

    @api.depends('manufacturer', 'manufacturer_pref')
    def _compute_display_name(self):
        for record in self:
            if record.manufacturer_pref:
                record.display_name = (f"[{record.manufacturer_pref}] "
                                       f"{record.manufacturer.name}")
            else:
                record.display_name = f"{record.manufacturer.name}"

    def _compute_product_variant_id(self):
        for record in self:
            if record.product_id:
                record.product_variant_id = record.product_id
            elif record.product_tmpl_id:
                record.product_variant_id = record.product_tmpl_id.product_variant_id
            else:
                record.product_variant_id = False

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if not res.get('product_tmpl_id') and res.get('product_id'):
            product_id = self.env['product.product'].browse(res['product_id'])
            res['product_tmpl_id'] = product_id.product_tmpl_id.id
        return res

    @api.depends('manufacturer', 'product_tmpl_id', 'product_id')
    def name_get(self):
        result = []
        for manufacturer in self:
            product_id = manufacturer.product_id or manufacturer.product_tmpl_id
            name = (f'{manufacturer.manufacturer_pref and "[%s] " % manufacturer.manufacturer_pref or ""}'
                    f'[{product_id.default_code}]{manufacturer.manufacturer.name}')
            result.append((manufacturer.id, name))
        return result
