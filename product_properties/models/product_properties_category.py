#  -*- coding: utf-8 -*-
#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _, Command
from .product_properties import _clean_website, MAGIC_FIELDS

_logger = logging.getLogger(__name__)


class ProductPropertiesCategory(models.Model):
    _name = "product.properties.category"
    _description = "Category Product properties"

    name = fields.Char('Property name', required=True, translate=True)
    applicability = fields.Selection([
        ('product', 'Product(o2m)'),
        ('productoo', 'Product(o2o)'),
        ('template', 'Product template(o2m)'),
        ('templateoo', 'Product template(o2o)'),
        ('product_set', 'Product set'),
    ],
        'Use for',
        required=True)
    lines_ids = fields.One2many(comodel_name='product.properties.category.lines',
                                inverse_name="categ_id",
                                string='Category properties')
    print_ids = fields.One2many('product.properties.print', 'categ_id', string='Category print properties')


class ProductPropertiesCategoryLines(models.Model):
    _name = "product.properties.category.lines"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Product Category lines properties"
    _order = "sequence, id"

    categ_id = fields.Many2one("product.properties.category", "Category", index=True, ondelete="cascade")
    product_categ_id = fields.Many2one("product.category", "Property Category", index=True)

    sequence = fields.Integer("Sequence",
                              default=10,
                              help="The first in the sequence is the default one.")

    name = fields.Many2one("product.properties.type", string="Property name", required=True)
    type_fields = fields.Selection(related="name.type_fields", required=True, store=True)

    type_float = fields.Float(related="name.type_float", store=True)
    type_char = fields.Char(related="name.type_char", store=True)
    type_int = fields.Integer(related="name.type_int", store=True)
    type_int_second = fields.Integer(related="name.type_int_second", store=True)
    type_eval = fields.Text(related="name.type_eval", store=True)
    type_currency = fields.Monetary(related="name.type_currency",
                                    currency_field="currency_id", store=True)

    type_date = fields.Date(related="name.type_date", store=True)
    type_range = fields.Char("Value Range in category", compute="_display_type_range")
    type_boolean = fields.Boolean(related="name.type_boolean", store=True)
    type_url = fields.Char(related="name.type_url", store=True)
    type_field = fields.Char(related='name.type_field', store=True)
    type_field_model_id = fields.Many2one(related="name.type_field_model_id",
                                          store=True,
                                          domain=lambda self: self.env['product.properties.type']._get_domain_type_field_model_id())
    type_field_target = fields.Many2one(related="name.type_field_target", store=True)
    type_package_id = fields.Many2one(related="name.type_package_id", store=True)
    type_package = fields.Char("Type package in category", compute="_display_type_package")
    dimensions_x = fields.Float(related="name.dimensions_x", store=True)
    dimensions_y = fields.Float(related="name.dimensions_y", store=True)
    dimensions_z = fields.Float(related="name.dimensions_z", store=True)
    type_uom_id = fields.Many2one(related="name.type_uom_id", store=True)
    type_dropdown_id = fields.Many2one(related="name.type_dropdown_id", store=True)
    # type_display = fields.Char("Value", compute=lambda self: self.env['product.properties']._display_type())
    # type_display_attrs = fields.Char("Value attrs", compute=lambda self: self.env['product.properties']._display_type())
    currency_id = fields.Many2one(related='name.currency_id', store=True)

    print_domain = fields.Text('Print domain')
    system_properties = fields.Boolean('System used')

    @api.onchange('name')
    def _onchange_name(self):
        if self.name.type_fields == 'field':
            self.type_field_model_id = self.name.type_field_model_id.id
            self.type_field_target = self.name.type_field_target.id
        else:
            self.type_field_model_id = False

    def _get_type_field(self):
        for field_value in self:
            field_value.type_field = False

    def _display_type_package(self):
        for record in self:
            record.type_package = record.type_package_id and record.type_package_id.name or ''

    def _display_type_range(self):
        for record in self:
            record.type_range = "-".join([str(record.type_int), str(record.type_int_second)])

    def _sanitize_vals(self, vals):
        if vals.get('type_url', False):
            vals['type_url'] = _clean_website(vals['type_url'])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sanitize_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._sanitize_vals(vals)
        return super(ProductPropertiesCategoryLines, self).write(vals)
