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

EUROCAR = [('euro1',  _('[EURO 1] July 1992')),
            ('euro2', _('[EURO 2] January 1996')),
            ('euro3', _('[EURO 3] January 2000')),
            ('euro4', _('[EURO 4] January 2005')),
            ('euro5', _('[EURO 5] September 2009')),
            ('euro6', _('[EURO 6] September 2014'))]

EUROCOM1 = [('euro1', _('[EURO 1] October 1994')),
            ('euro2', _('[EURO 2] January 1998')),
            ('euro3', _('[EURO 3] January 2000')),
            ('euro4', _('[EURO 4] January 2005')),
            ('euro5', _('[EURO 5] September 2009')),
            ('euro6', _('[EURO 6] September 2014'))]

EUROCOM2 = [('euro1', _('[EURO 1] October 1994')),
            ('euro2', _('[EURO 2] January 1998')),
            ('euro3', _('[EURO 3] January 2001')),
            ('euro4', _('[EURO 4] January 2006')),
            ('euro5', _('[EURO 5] September 2010')),
            ('euro6', _('[EURO 6] September 2015'))]

EUROCOM3 = [('euro1', _('[EURO 1] October 1994')),
            ('euro2', _('[EURO 2] January 1998')),
            ('euro3', _('[EURO 3] January 2001')),
            ('euro4', _('[EURO 4] January 2006')),
            ('euro5', _('[EURO 5] September 2010')),
            ('euro6', _('[EURO 6] September 2015'))]

TYPES = [('char', _('String')),
         ('float', _('Float')),
         ('int', _('Integer')),
         ('range', _('Range')),
         ('boolean', _('Yse/No')),
         ('tank', _('Tank')),
         ('vehicle', _('Type of vehicle')),
         ('power', _('Range Еngine power')),
         ('year', _('Year of manufacture')),
         ('euro', _('European emission standards'))]

CARTYPE = [('M', _('Vehicles with at least 4 wheels designed to carry passengers - essentially, cars.')),
            ('N', _('Vehicles designed to carry goods, grouped by size. Essentially lorries and vans.'))]

class ProductTechnicalProperties(models.Model):
    _name = "product.technical.properties"
    _description = "Technical properties"

    @api.multi
    def _display_type_power_range(self):
        for record in self:
            record.type_power_range = "-".join([str(record.type_power), str(record.type_power_second)])

    @api.multi
    def _display_type_range(self):
        for record in self:
            record.type_range = "-".join([str(record.type_int), str(record.type_int_second)])

    @api.multi
    def _display_type_tank(self):
        for record in self:
            record.type_tank = record.type_tank_id and record.type_tank_id.name or ''

    @api.multi
    def _display_type(self):
        for record in self:
            if record.name:
                record.type_display = "%s%s" % (record["type_%s" % record.type_fields] or '', record.type_uom_id and record.type_uom_id.name or '')
            else:
                record.type_display = ''
            if record.name.type_fields == 'tank':
                record.type_display_attrs = "x".join([str(record.dimensions_x), str(record.dimensions_y), str(record.dimensions_z)]) + "(%s)cc" % record.volume
            else:
                record.type_display_attrs = ''

    @api.multi
    def _get_euro(self):
        if self.type_cars and self.type_cars == 'M':
            return EUROCAR
        return EUROCOM3


    #categ_id = fields.Many2one("product.electrical", "Category", default=lambda self, *a: self._context.get("default_categ_id", False))
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', default=lambda self, *a: self._context.get("default_product_tmpl_id", False))
    name = fields.Many2one("product.technical.properties.type", string="Property name", required=True)
    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    type_fields = fields.Selection(TYPES, string="Type properties", required=True)
    type_euro = fields.Selection(compute=_get_euro, string="Value Emission")
    type_cars = fields.Selection(CARTYPE, string="Category car")
    type_float = fields.Float(string="Value for Float")
    type_char = fields.Char(string="Value for Char")
    type_int = fields.Integer(string="Value for Int")
    type_int_second = fields.Integer("Value for Second Int")
    type_range = fields.Char("Value Range", compute='_display_type_range')
    type_boolean = fields.Boolean("Value for Boolean")
    type_tank_id = fields.Many2one("product.technical.properties.tank", string="Value for Tank")
    type_tank = fields.Char("Value Demension", compute='_display_type_tank')
    type_power_range = fields.Char("power Range", compute='_display_type_power_range')
    type_power = fields.Integer("Value for Power low threshold")
    type_power_second = fields.Integer("Value for Power high threshold")
    dimensions_x = fields.Float(string="X Dimensions")
    dimensions_y = fields.Float(string="Y Dimensions")
    dimensions_z = fields.Float(string="Z Dimensions")
    #type_euro = fields.Selection(MSL, string="Value Emission")
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
    type_uom_id = fields.Many2one("product.technical.properties.uom", string="UOM Name", ondelete="restrict")
    type_display = fields.Char("Value", compute='_display_type')
    type_display_attrs = fields.Char("Value attrs", compute='_display_type')


    @api.onchange('type_tank_id')
    def _onchange_type_tank_id(self):
        self.image = self.type_tank_id.image
        self.image_medium = self.type_tank_id.image_medium
        self.image_small = self.type_tank_id.image_small
        self.dimensions_x = self.type_tank_id.dimensions_x
        self.dimensions_y = self.type_tank_id.dimensions_y
        self.dimensions_z = self.type_tank_id.dimensions_z
        self.volume = self.type_tank_id.volume
        return {'value': {'image': self.type_tank_id.image, 'image_medium': self.type_tank_id.image_medium, 'image_small': self.type_tank_id.image_small,
                          'dimensions_x': self.type_tank_id.dimensions_x, 'dimensions_y': self.type_tank_id.dimensions_y, 'dimensions_z': self.type_tank_id.dimensions_z, 'volume': self.type_tank_id.volume}}

    @api.model
    def create(self, vals):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        # TDE FIXME: context brol
        tools.image_resize_images(vals)
        return super(ProductTechnicalProperties, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(ProductTechnicalProperties, self).write(vals)

class ProductTechnical(models.Model):
    _name = "product.technical"
    _description = "Product Technical properties"

    name = fields.Char('Property name', required=True)
    #product_template_ids = fields.One2many('product.template', 'electrical_properties_id', 'Product template',
    #    change_default=True, default=lambda self, *a: self._context.get("default_electrical_properties_id", False),
    #    required=True)

    #properties_ids = fields.One2many(comodel_name='product.electrical.properties',
    #    inverse_name="categ_id",
    #    string='Electrical properties', ondelete='restrict')
    lines_ids = fields.One2many(comodel_name='product.technical.lines',
        inverse_name="categ_id",
        string='Technical properties', ondelete='restrict')


class ProductTechnicalLine(models.Model):
    _name = "product.technical.lines"
    _description = "Product technical lines properties"

    @api.multi
    def _display_type_range(self):
        for record in self:
            record.type_range = "-".join([str(record.type_int), str(record.type_int_second)])

    @api.multi
    def _display_type_tank(self):
        for record in self:
            record.type_tank = record.type_tank_id and record.type_tank_id.name or ''

    @api.multi
    def _display_type(self):
        for record in self:
            if record.name:
                record.type_display = "%s%s" % (record["type_%s" % record.name.type_fields] or '', record.type_uom_id and record.type_uom_id.name or '')
            else:
                record.type_display = ''
            if record.name.type_fields == 'tank':
                record.type_display_attrs = "x".join([str(record.dimensions_x), str(record.dimensions_y), str(record.dimensions_z)]) + " (%s)cc" % record.tank
            else:
                record.type_display_attrs = ''

    @api.multi
    def _get_euro(self):
        if self.type_cars and self.type_cars == 'M':
            return EUROCAR
        return EUROCOM3

    categ_id = fields.Many2one("product.technical", "Category", default=lambda self, *a: self._context.get("default_categ_id", False))
    name = fields.Many2one("product.technical.properties.type", string="Property name", required=True)
    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    type_fields = fields.Selection(related="name.type_fields", string="Type properties", required=True, store=True)
    type_cars = fields.Selection(CARTYPE, string="Category car")
    type_float = fields.Float(related="name.type_float", string="Value for Float", store=True)
    type_char = fields.Char(related="name.type_char", string="Value for Char", store=True)
    type_int = fields.Integer(related="name.type_int",string="Value for Int", store=True)
    type_int_second = fields.Integer(related="name.type_int_second", string="Value for Second Int")
    type_range = fields.Char("Value Range", compute='_display_type_range')
    type_boolean = fields.Boolean(related="name.type_boolean", string="Value for Boolean")

    type_tank_id = fields.Many2one(related="name.type_tank_id", string="Value for Tank", store=True)
    type_tank = fields.Char("Value Demension", compute='_display_type_tank')
    type_tank_dimensions_x = fields.Float(related="name.dimensions_x", string="X Dimensions", store=True)
    type_tank_dimensions_y = fields.Float(related="name.dimensions_y", string="Y Dimensions", store=True)
    type_tank_dimensions_z = fields.Float(related="name.dimensions_z", string="Z Dimensions", store=True)
    type_tank_volume = fields.Float(related="name.volume", string="Volume (L)", store=True)

    type_power = fields.Integer("Value for Power low threshold")
    type_power_second = fields.Integer("Value for Power high threshold")

    type_euro = fields.Selection(compute=_get_euro, string="Value Emission")
    type_uom_id = fields.Many2one(related="name.type_uom_id", string="UOM Name", store=True)

    type_power_engine_id = fields.Many2one(related="name.type_power_engine_id", string="Power Engine Type", store=True)
    type_power_engine_cylinders = fields.Float(related="name.type_power_engine_cylinders", string="Number of cylinders", store=True)
    type_power_engine_type = fields.Float(related="name.type_power_engine_type", string="Type of engine", store=True)
    type_power_engine_power = fields.Float(related="name.type_power_engine_power", string="Power of engine", store=True)
    type_power_engine_year = fields.Float(related="name.type_power_engine_year", string="Year of engine", store=True)

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
        return super(ProductTechnicalLine, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(ProductTechnicalLine, self).write(vals)


class ProductTechnicalPropertiesType(models.Model):
    _name = "product.technical.properties.type"
    _description = "The technical types"


    @api.multi
    def _get_euro(self):
        if self.type_cars and self.type_cars == 'M':
            return EUROCAR
        return EUROCOM3

    name = fields.Char('Type Name', required=True, index=True)
    type_fields = fields.Selection(TYPES, string="Type properties", required=True, default='char')
    type_float = fields.Float("Value for Float")
    type_char = fields.Char("Value for Char")
    type_int = fields.Integer("Value for Int")
    type_int_second = fields.Integer("Value for Second Int")
    type_boolean = fields.Boolean("Value for Boolean")
    type_power = fields.Integer("Value for Power low threshold")
    type_power_second = fields.Integer("Value for Power high threshold")
    type_tank_id = fields.Many2one("product.technical.properties.tank", string="Value for Tank")
    dimensions_x = fields.Float(related="type_tank_id.dimensions_x", string="X Dimensions")
    dimensions_y = fields.Float(related="type_tank_id.dimensions_y", string="Y Dimensions")
    dimensions_z = fields.Float(related="type_tank_id.dimensions_z", string="Z Dimensions")
    volume = fields.Float(related="type_tank_id.volume", string="Volume (L)")
    type_euro = fields.Selection(copune=_get_euro, string="Value Emission",)
    type_cars = fields.Selection(CARTYPE, string="Category car")
    type_uom_id = fields.Many2one("product.technical.properties.uom", string="UOM Name")

class ProductTechnicalPropertiesUom(models.Model):
    _name = "product.technical.properties.uom"
    _description = "The technical units"

    name = fields.Char('UOM Name', required=True, index=True)

class ProductTechnicalPropertiesTank(models.Model):
    _name = "product.technical.properties.tank"
    _description = "The technical tank/volume"

    name = fields.Char('Tank Name', required=True, index=True)
    dimensions_x = fields.Float("X Dimensions")
    dimensions_y = fields.Float("Y Dimensions")
    dimensions_z = fields.Float("Z Dimensions")
    volume = fields.Float("Volume (L)")
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
