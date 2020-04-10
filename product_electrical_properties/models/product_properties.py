# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import psycopg2

from odoo.addons import decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, except_orm
from odoo.tools import pycompat

import logging
_logger = logging.getLogger(__name__)

MSL = [('msl6',   '[MSL6] Mandatory Bake before use'),
        ('msl5a', '[MSL5A] 24 hours'),
        ('msl5',  '[MSL5] 48 hours'),
        ('msl4',  '[MSL4] 72 hours'),
        ('msl3',  '[MSL3] 168 hours'),
        ('msl2a', '[MSL2A] 4 weeks'),
        ('msl2',  '[MSL2] 1 year'),
        ('msl1',  '[MSL1] Unlimited')]

TYPES = [('char','String'),
         ('float', 'Float'),
         ('int', 'Integer'),
         ('range', 'Range'),
         ('boolean', 'Yse/No'),
         ('package', 'Package'),
         ('msl', 'Moisture sensitivity level')]


class ProductElectricalProperties(models.Model):
    _name = "product.electrical.properties"
    _description = "Electrical properties"

    @api.multi
    def _display_type_range(self):
        for record in self:
            record.type_range = "-".join([str(record.type_int), str(record.type_int_second)])

    @api.multi
    def _display_type_package(self):
        for record in self:
            record.type_package = record.type_package_id and record.type_package_id.name or ''

    @api.multi
    def _display_type(self):
        for record in self:
            if record.name:
                record.type_display = "%s%s" % (record["type_%s" % record.type_fields] or '', record.type_uom_id and record.type_uom_id.name or '')
            else:
                record.type_display = ''
            if record.name.type_fields == 'package':
                record.type_display_attrs = "x".join([str(record.dimensions_x), str(record.dimensions_y), str(record.dimensions_z)])
            else:
                record.type_display_attrs = ''

    #categ_id = fields.Many2one("product.electrical", "Category", default=lambda self, *a: self._context.get("default_categ_id", False))
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', default=lambda self, *a: self._context.get("default_product_tmpl_id", False))
    name = fields.Many2one("product.electrical.properties.type", string="Property name", required=True)
    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    type_fields = fields.Selection(TYPES, string="Type properties", required=True)
    type_float = fields.Float(string="Value for Float")
    type_char = fields.Char(string="Value for Char")
    type_int = fields.Integer(string="Value for Int")
    type_int_second = fields.Integer("Value for Second Int")
    type_range = fields.Char("Value Range", compute='_display_type_range')
    type_boolean = fields.Boolean("Value for Boolean")
    type_package_id = fields.Many2one("product.electrical.properties.package", string="Value for Package")
    type_package = fields.Char("Value Range", compute='_display_type_package')
    dimensions_x = fields.Float(string="X Dimensions")
    dimensions_y = fields.Float(string="Y Dimensions")
    dimensions_z = fields.Float(string="Z Dimensions")
    type_msl = fields.Selection(MSL, string="Value MSL")
    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the product, limited to 1024x1024px.")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    type_uom_id = fields.Many2one("product.electrical.properties.uom", string="UOM Name", ondelete="restrict")
    type_display = fields.Char("Value", compute='_display_type')
    type_display_attrs = fields.Char("Value attrs", compute='_display_type')


    @api.onchange('type_package_id')
    def _onchange_type_package_id(self):
        self.image = self.type_package_id.image
        self.image_medium = self.type_package_id.image_medium
        self.image_small = self.type_package_id.image_small
        self.dimensions_x = self.type_package_id.dimensions_x
        self.dimensions_y = self.type_package_id.dimensions_y
        self.dimensions_z = self.type_package_id.dimensions_z
        return {'value': {'image': self.type_package_id.image, 'image_medium': self.type_package_id.image_medium, 'image_small': self.type_package_id.image_small,
                          'dimensions_x': self.type_package_id.dimensions_x, 'dimensions_y': self.type_package_id.dimensions_y, 'dimensions_z': self.type_package_id.dimensions_z}}

    @api.model
    def create(self, vals):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        # TDE FIXME: context brol
        tools.image_resize_images(vals)
        return super(ProductElectricalProperties, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(ProductElectricalProperties, self).write(vals)

class ProductElectrical(models.Model):
    _name = "product.electrical"
    _description = "Product Electrical properties"

    name = fields.Char('Property name', required=True)
    #product_template_ids = fields.One2many('product.template', 'electrical_properties_id', 'Product template',
    #    change_default=True, default=lambda self, *a: self._context.get("default_electrical_properties_id", False),
    #    required=True)

    #properties_ids = fields.One2many(comodel_name='product.electrical.properties',
    #    inverse_name="categ_id",
    #    string='Electrical properties', ondelete='restrict')
    lines_ids = fields.One2many(comodel_name='product.electrical.lines',
        inverse_name="categ_id",
        string='Electrical properties', ondelete='restrict')


class ProductElectricalLine(models.Model):
    _name = "product.electrical.lines"
    _description = "Product Electrical lines properties"

    @api.multi
    def _display_type_range(self):
        for record in self:
            record.type_range = "-".join([str(record.type_int), str(record.type_int_second)])

    @api.multi
    def _display_type_package(self):
        for record in self:
            record.type_package = record.type_package_id and record.type_package_id.name or ''

    @api.multi
    def _display_type(self):
        for record in self:
            if record.name:
                record.type_display = "%s%s" % (record["type_%s" % record.name.type_fields] or '', record.type_uom_id and record.type_uom_id.name or '')
            else:
                record.type_display = ''
            if record.name.type_fields == 'package':
                record.type_display_attrs = "x".join([str(record.dimensions_x), str(record.dimensions_y), str(record.dimensions_z)])
            else:
                record.type_display_attrs = ''

    categ_id = fields.Many2one("product.electrical", "Category", default=lambda self, *a: self._context.get("default_categ_id", False))
    name = fields.Many2one("product.electrical.properties.type", string="Property name", required=True)
    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    type_fields = fields.Selection(related="name.type_fields", string="Type properties", required=True, store=True)
    type_float = fields.Float(related="name.type_float", string="Value for Float", store=True)
    type_char = fields.Char(related="name.type_char", string="Value for Char", store=True)
    type_int = fields.Integer(related="name.type_int",string="Value for Int", store=True)
    type_int_second = fields.Integer(related="name.type_int_second", string="Value for Second Int")
    type_range = fields.Char("Value Range", compute='_display_type_range')
    type_boolean = fields.Boolean(related="name.type_boolean", string="Value for Boolean")
    type_package_id = fields.Many2one(related="name.type_package_id", string="Value for Package", store=True)
    type_package = fields.Char("Value Range", compute='_display_type_package')
    dimensions_x = fields.Float(related="name.dimensions_x", string="X Dimensions", store=True)
    dimensions_y = fields.Float(related="name.dimensions_y", string="Y Dimensions", store=True)
    dimensions_z = fields.Float(related="name.dimensions_z", string="Z Dimensions", store=True)
    type_msl = fields.Selection(MSL, string="Value MSL")
    type_uom_id = fields.Many2one(related="name.type_uom_id", string="UOM Name", store=True)
    type_display = fields.Char("Value", compute='_display_type')
    type_display_attrs = fields.Char("Value attrs", compute='_display_type')
    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the product, limited to 1024x1024px.")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")

    @api.model
    def create(self, vals):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        # TDE FIXME: context brol
        tools.image_resize_images(vals)
        return super(ProductElectricalLine, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(ProductElectricalLine, self).write(vals)


class ProductElectricalPropertiesType(models.Model):
    _name = "product.electrical.properties.type"
    _description = "The electrical types"

    name = fields.Char('Type Name', required=True, index=True)
    type_fields = fields.Selection(TYPES, string="Type properties", required=True, default='char')
    type_float = fields.Float("Value for Float")
    type_char = fields.Char("Value for Char")
    type_int = fields.Integer("Value for Int")
    type_int_second = fields.Integer("Value for Second Int")
    type_boolean = fields.Boolean("Value for Boolean")
    type_package_id = fields.Many2one("product.electrical.properties.package", string="Value for Package")
    dimensions_x = fields.Float(related="type_package_id.dimensions_x", string="X Dimensions")
    dimensions_y = fields.Float(related="type_package_id.dimensions_y", string="Y Dimensions")
    dimensions_z = fields.Float(related="type_package_id.dimensions_z", string="Z Dimensions")
    type_msl = fields.Selection(MSL, string="Value MSL",)
    type_uom_id = fields.Many2one("product.electrical.properties.uom", string="UOM Name")

class ProductElectricalPropertiesUom(models.Model):
    _name = "product.electrical.properties.uom"
    _description = "The electrical units"

    name = fields.Char('UOM Name', required=True, index=True)

class ProductElectricalPropertiesPackage(models.Model):
    _name = "product.electrical.properties.package"
    _description = "The electrical packages/corpuses"

    name = fields.Char('Package Name', required=True, index=True)
    dimensions_x = fields.Float("X Dimensions")
    dimensions_y = fields.Float("Y Dimensions")
    dimensions_z = fields.Float("Z Dimensions")
    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the product, limited to 1024x1024px.")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
