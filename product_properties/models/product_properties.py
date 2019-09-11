# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import psycopg2
import json
from werkzeug import urls

from odoo.addons import decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, UserError, except_orm
from odoo.tools import pycompat

import logging
_logger = logging.getLogger(__name__)


TYPES = [('char', _('String')),
         ('float', _('Float')),
         ('int', _('Integer')),
         ('date', _('Date')),
         ('range', _('Range')),
         ('boolean', _('Yes/No')),
         ('package', _('Package')),
         ('dropdown_id', _('Dropdown menu')),
         ('pricelist', _('Linked width pricelist')),
         ('url', _('Base on URL')),
         ('field', _('Base on field')),
         ('lot', _('Base on LOT/SN')),
         ('use_date', _('Base on Use date')),
         ('gs1', _('Base on GS1(UDI)')),
         ]

class ProductPropertiesPrint(models.Model):
    _name = "product.properties.print"
    _description = "Product properties for printing"
    _order = "system_properties, sequence"

    name = fields.Many2one("product.properties.type", string="Property name", required=True, translate=True)
    print = fields.Boolean('Print')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('product.properties.print'))
    categ_id = fields.Many2one("product.properties.category", "Category", index=True)

    partner_id = fields.Many2one('res.partner', string='Partner', index=True)
    order_id = fields.Many2one("sale.order", string="Sale order", index=True)
    invoice_id = fields.Many2one("account.invoice", string="Invoice", index=True)
    system_properties = fields.Boolean('System used')
    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")

    def get_print_properties(self):
        return [x.name.id for x in self if x.print]

    @api.multi
    def unlink(self):
        for properties in self:
            if properties.system_properties:
                raise UserError(_('You cannot delete system properties.'))
        return super(ProductPropertiesPrint, self).unlink()


class ProductProperties(models.Model):
    _name = "product.properties"
    _description = "Product properties"

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
            if record.name.type_fields == 'dropdown_id':
                record.type_display = record.type_dropdown_id and record.type_dropdown_id.name_get()[0][1] or ''
            elif record.name and "type_%s" % record.type_fields in self._fields:
                record.type_display = "%s %s" % (getattr(record, "type_%s" % record.type_fields) or '', record.type_uom_id and record.type_uom_id.name or '')
            else:
                record.type_display = ''
            if record.name.type_fields == 'package':
                record.type_display_attrs = "x".join([str(record.dimensions_x), str(record.dimensions_y), str(record.dimensions_z)])
            else:
                record.type_display_attrs = ''
            if record.name.type_fields == 'field' and record.product_id == False:
                record.type_display = record.type_field_target.field_description

    def _get_type_field_model_id(self):
        return json.dumps(self.env['product.properties.type']._get_type_field_model_id())

    product_tmpl_id = fields.Many2one('product.template', 'Product Template', ondelete='restrict')
    product_id = fields.Many2one('product.product', 'Product', ondelete='restrict')

    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")

    name = fields.Many2one("product.properties.type", string="Property name", required=True, translate=True)
    type_fields = fields.Selection(related="name.type_fields", string="Type properties", required=True, store=True)

    categ_id = fields.Many2one('product.properties.category', string='Category Properties')

    type_float = fields.Float(string="Value for Float")
    type_char = fields.Char(string="Value for Char")
    type_int = fields.Integer(string="Value for Int")
    type_int_second = fields.Integer("Value for Second Int")
    type_date = fields.Date(string="Value for Date")
    type_range = fields.Char("Value Range", compute='_display_type_range')
    type_boolean = fields.Boolean("Value for Boolean")
    type_url = fields.Char(help="URL")

    type_field = fields.Char(help="Field", compute="_get_type_field")
    type_field_name = fields.Char(help="Field", compute="_get_type_field_properties", inverse="_set_type_field_name")
    type_field_ttype = fields.Char(help="Field", compute="_get_type_field_properties", inverse="_set_type_field_ttype")
    type_field_model = fields.Char(help="Field", compute="_get_type_field_properties", inverse="_set_type_field_model")
    model_obj_id = fields.Integer('Model object holder id', compute="_get_type_field_properties", inverse="_set_model_obj_id")

    type_field_model_id = fields.Many2one('ir.model', string='Target/Source Odoo model', domain=_get_type_field_model_id)
    type_field_target = fields.Many2one('ir.model.fields', string='Target/Source Odoo field',
                                  help="""Choice target/source field for collection data.
                                  target/source in odoo model.""",
                                  domain="[('model_id', '=', type_field_model_id), ('ttype', 'in', ['char', 'many2one']), ('name', 'not in', ('id', 'create_uid','create_date', 'write_date', 'write_uid', '__last_update', 'lines'))]")

    type_package_id = fields.Many2one("product.properties.package", string="Value for Package")
    type_package = fields.Char("Value Range", compute='_display_type_package')
    dimensions_x = fields.Float(string="X Dimensions")
    dimensions_y = fields.Float(string="Y Dimensions")
    dimensions_z = fields.Float(string="Z Dimensions")
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
    type_uom_id = fields.Many2one("product.properties.uom", string="UOM Name", ondelete="restrict")
    type_dropdown_id = fields.Many2one("product.properties.dropdown", string="Dropdown")
    type_display = fields.Char("Value", compute='_display_type')
    type_display_attrs = fields.Char("Value attrs", compute='_display_type')

    def _clean_website(self, website):
        url = urls.url_parse(website)
        if not url.scheme:
            if not url.netloc:
                url = url.replace(netloc=url.path, path='')
            website = url.replace(scheme='http').to_url()
        return website

    @api.multi
    def _get_type_field_properties(self):
        for field_name in self:
            if not field_name.type_field_name:
                field_name.type_field_name = field_name.type_field_target.name
            if not field_name.type_field_ttype:
                field_name.type_field_ttype = field_name.type_field_target.ttype
            if not field_name.type_field_model:
                field_name.type_field_model = field_name.type_field_target.model_id.model
            if not field_name.model_obj_id and field_name.type_field_model == 'product.product':
                field_name.model_obj_id = field_name.product_id.id
            elif not field_name.model_obj_id and field_name.type_field_model == 'product.template':
                field_name.model_obj_id = field_name.product_tmpl_id.id

    def _set_type_field_name(self):
        for rec in self:
            if not rec.type_field_name:
                rec.type_field_name = rec.type_field_target.name

    def _set_type_field_ttype(self):
        for rec in self:
            if not rec.type_field_ttype:
                rec.type_field_ttype = rec.type_field_target.ttype

    def _set_type_field_model(self):
        for rec in self:
            if not rec.type_field_model:
                rec.type_field_model = rec.type_field_target.model_id.model

    def _set_model_obj_id(self):
        for rec in self:
            if not rec.model_obj_id and rec.type_field_model == 'product.product':
                rec.model_obj_id = rec.product_id.id
            elif not rec.model_obj_id and rec.type_field_model == 'product.template':
                rec.model_obj_id = rec.product_tmpl_id.id

    @api.one
    def get_type_field_properties(self, line):
        if line._name == 'product.pricelist.item':
            self.model_obj_id = line.pricelist_id.id
        super(ProductProperties, self).get_type_field_properties(line)

    @api.multi
    def _get_type_field(self):
        for field_value in self:
            if field_value.type_field_target:
                model_obj = field_value.type_field_model
                ttype = field_value.type_field_ttype
                name = field_value.type_field_name
                id = field_value.model_obj_id
                if not id:
                    id = field_value.name.id
                    model_obj = 'product.properties.type'
                    ttype = 'char'
                    name = 'name'
                model = self.env[model_obj].browse(id)
                if ttype == 'char':
                    field_value.type_field = getattr(model, name)
                elif ttype == 'many2one':
                    field = getattr(model, name)
                    relation = field_value.type_field_target.relation
                    model = self.env[relation].browse([field.id])
                    if 'display_name' in model._fields:
                        field_value.type_field = getattr(model, 'display_name')
                    else:
                        field_value.type_field = getattr(model, 'name')
            else:
                field_value.type_field = False

    @api.onchange('name')
    def _onchange_name(self):
        if self.name.type_fields == 'field':
            self.type_field_model_id = self.name.type_field_model_id.id
            self.type_field_target = self.name.type_field_target.id
        else:
            self.type_field_model_id = False

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
        if vals.get('type_url'):
            vals['type_url'] = self._clean_website(vals['type_url'])
        return super(ProductProperties, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        if vals.get('type_url'):
            vals['type_url'] = self._clean_website(vals['type_url'])
        return super(ProductProperties, self).write(vals)


class ProductPropertiesCategory(models.Model):
    _name = "product.properties.category"
    _description = "Product properties"

    name = fields.Char('Property name', required=True, translate=True)
    lines_ids = fields.One2many(comodel_name='product.properties.category.lines',
        inverse_name="categ_id",
        string='Category properties', ondelete='restrict')
    print_ids = fields.One2many('product.properties.print', 'categ_id', string='Category print properties')
    #properties_ids = fields.Many2many('product.properties', relation='product_properties_cat', column1='categ_id', column2='properties_id', string='Product Properties')


class ProductCategory(models.Model):
    _inherit = "product.category"

    product_properties_ids = fields.One2many(comodel_name='product.properties.category.lines',
        inverse_name="product_categ_id",
        string='Category properties', ondelete='restrict')


class ProductPropertiesCategoryLines(models.Model):
    _name = "product.properties.category.lines"
    _description = "Product Category lines properties"
    _order = "sequence, id"

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
            if record.name.type_fields == 'dropdown_id':
                record.type_display = record.type_dropdown_id and record.type_dropdown_id.name_get()[0][1] or ''
            if record.name and "type_%s" % record.type_fields in self._fields:
                record.type_display = "%s %s" % (record["type_%s" % record.type_fields] or '', record.type_uom_id and record.type_uom_id.name or '')
            else:
                record.type_display = ''
            if record.name.type_fields == 'package':
                record.type_display_attrs = "x".join([str(record.dimensions_x), str(record.dimensions_y), str(record.dimensions_z)])
            else:
                record.type_display_attrs = ''
            if record.name.type_fields == 'field':
                record.type_display = record.type_field_target.field_description

    def _get_type_field_model_id(self):
        return self.env['product.properties.type']._get_type_field_model_id()

    categ_id = fields.Many2one("product.properties.category", "Category", index=True)
    product_categ_id = fields.Many2one("product.category", "Category", index=True)

    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")

    name = fields.Many2one("product.properties.type", string="Property name", required=True)
    type_fields = fields.Selection(related="name.type_fields", string="Type properties", required=True, store=True)

    type_float = fields.Float(related="name.type_float", string="Value for Float", store=True)
    type_char = fields.Char(related="name.type_char", string="Value for Char", store=True)
    type_int = fields.Integer(related="name.type_int",string="Value for Int", store=True)
    type_int_second = fields.Integer(related="name.type_int_second", string="Value for Second Int")
    type_date = fields.Date(string="Value for Date")
    type_range = fields.Char("Value Range", compute='_display_type_range')
    type_boolean = fields.Boolean(related="name.type_boolean", string="Value for Boolean")
    type_url = fields.Char(help="URL")
    type_field = fields.Char(help="Field", compute="_get_type_field")
    type_field_model_id = fields.Many2one('ir.model', string='Target/Source Odoo model', domain=_get_type_field_model_id)
    type_field_target = fields.Many2one('ir.model.fields', string='Target/Source Odoo field',
                                  help="""Choice target/source field for collection data.
                                  target/source in odoo model.""",
                                  domain="[('model_id', '=', type_field_model_id), ('ttype', 'in', ['char', 'many2one']), ('name', 'not in', ('id', 'create_uid','create_date', 'write_date', 'write_uid', '__last_update', 'lines'))]")
    type_package_id = fields.Many2one(related="name.type_package_id", string="Value for Package", store=True)
    type_package = fields.Char("Value Range", compute='_display_type_package')
    dimensions_x = fields.Float(related="name.dimensions_x", string="X Dimensions", store=True)
    dimensions_y = fields.Float(related="name.dimensions_y", string="Y Dimensions", store=True)
    dimensions_z = fields.Float(related="name.dimensions_z", string="Z Dimensions", store=True)
    type_uom_id = fields.Many2one(related="name.type_uom_id", string="UOM Name", store=True)
    type_dropdown_id = fields.Many2one("product.properties.dropdown", string="Dropdown")
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
    print_domain = fields.Text('Print domain')
    system_properties = fields.Boolean('System used')

    @api.onchange('name')
    def _onchange_name(self):
        if self.name.type_fields == 'field':
            self.type_field_model_id = self.name.type_field_model_id.id
            self.type_field_target = self.name.type_field_target.id
        else:
            self.type_field_model_id = False

    def _clean_website(self, website):
        url = urls.url_parse(website)
        if not url.scheme:
            if not url.netloc:
                url = url.replace(netloc=url.path, path='')
            website = url.replace(scheme='http').to_url()
        return website

    @api.multi
    def _get_type_field(self):
        for field_value in self:
            field_value.type_field = False

    @api.model
    def create(self, vals):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        # TDE FIXME: context brol
        tools.image_resize_images(vals)
        if vals.get('type_url'):
            vals['type_url'] = self._clean_website(vals['type_url'])
        return super(ProductPropertiesCategoryLines, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        if vals.get('type_url'):
            vals['type_url'] = self._clean_website(vals['type_url'])
        return super(ProductPropertiesCategoryLines, self).write(vals)


class ProductPropertiesType(models.Model):
    _name = "product.properties.type"
    _description = "The Properties types"

    def _get_type_field_model_id(self):
        return [('model', 'in', ['product.product', 'product.template', 'product.pricelist.item', 'sale.order.line',
                                 'account.invoice.line', 'purchase.order.line', 'stock.move.line'])]

    name = fields.Char('Type Name', required=True, index=True, translate=True)
    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    type_fields = fields.Selection(TYPES, string="Type properties", required=True, default='char')
    type_float = fields.Float("Value for Float")
    type_char = fields.Char("Value for Char")
    type_int = fields.Integer("Value for Int")
    type_int_second = fields.Integer("Value for Second Int")
    type_date = fields.Date(string="Value for Date")
    type_boolean = fields.Boolean("Value for Boolean")
    type_url = fields.Char(help="URL")
    type_field = fields.Char(help="Field", compute="_get_type_field")
    type_field_model_id = fields.Many2one('ir.model', string='Target/Source Odoo model', domain=_get_type_field_model_id)
    type_field_target = fields.Many2one('ir.model.fields', string='Target/Source Odoo field',
                                  help="""Choice target/source field for collection data.
                                  target/source in odoo model.""",
                                  domain="[('model_id', '=', type_field_model_id), ('name', 'not in', ('id', 'create_uid','create_date', 'write_date', 'write_uid', '__last_update', 'lines'))]")
    type_package_id = fields.Many2one("product.properties.package", string="Value for Package")
    dimensions_x = fields.Float("X Dimensions")
    dimensions_y = fields.Float("Y Dimensions")
    dimensions_z = fields.Float("Z Dimensions")
    type_uom_id = fields.Many2one("product.properties.uom", string="UOM Name")
    type_dropdown_id = fields.Many2one("product.properties.dropdown", string="Dropdown")

    def get_type_field_model_id(self, domain=False):
        if not domain:
            domain = [('model', 'in', ['product.product', 'product.template', 'product.pricelist.item'])]
        return super(ProductPropertiesType, self).get_type_field_model_id(domain)

    @api.multi
    def _get_type_field(self):
        for field_value in self:
            if field_value.type_field_target:
                model = self.env[field_value.type_field_target.model_id.model]
                field_value.type_field = getattr(model, field_value.type_field_target.name)
            else:
                field_value.type_field = False

    def _clean_website(self, website):
        url = urls.url_parse(website)
        if not url.scheme:
            if not url.netloc:
                url = url.replace(netloc=url.path, path='')
            website = url.replace(scheme='http').to_url()
        return website

    def get_product_properties_print(self, line, product, properties_print=False, lot_ids=False, description=False):
        res = {}
        ret = []
        print_ids = [x.name.id for x in properties_print if x.print]
        for prop_line in product.tproduct_properties_ids:
            if properties_print and prop_line.name.id in print_ids:
                if line and prop_line.type_field_name in line._fields:
                    prop_line.type_field_model = line._name
                    prop_line.model_obj_id = line.id
                if lot_ids and prop_line.name.type_fields == 'lot':
                    res[prop_line.name.name] = {'value': lots_ids and '-'.join([x.name for x in lot_ids]) or '', 'attrs': False, 'image': False}
                elif lot_ids and line.name.type_fields == 'use_date':
                    res[prop_line.name.name] = {'value': lots_ids and '-'.join(['%s:%s' % (x.name, x.use_date) for x in lot_ids]) or '', 'attrs': False, 'image': False}
                elif lot_ids and prop_line.name.type_fields == 'gs1':
                    res[prop_line.name.name] = {'value': lots_ids and '-'.join([x.gs1 for x in lot_ids]) or '', 'attrs': False, 'image': False}
                elif prop_line.name.type_fields == 'pricelist':
                    prop_line.type_field_model = line._name
                    prop_line.model_obj_id = line.id
                    prop_line.type_field_ttype = 'many2one'
                    prop_line.type_field_name = 'pricelist_id'
                    res[prop_line.name.name] = {'value': prop_line.type_display, 'attrs': prop_line.type_display_attrs,
                                                'image': prop_line.image_small}
                else:
                    res[prop_line.name.name] = {'value': prop_line.type_display, 'attrs': prop_line.type_display_attrs, 'image': prop_line.image_small}
        for prop_line in product.product_properties_ids:
            if properties_print and prop_line.name.id in print_ids:
                if line and prop_line.type_field_name in line._fields:
                    prop_line.type_field_model = line._name
                    prop_line.model_obj_id = line.id
                if lot_ids and prop_line.name.type_fields == 'lot':
                    res[prop_line.name.name] = {'value': lots_ids and '-'.join([x.name for x in lot_ids]) or '', 'attrs': False, 'image': False}
                elif lot_ids and prop_line.name.type_fields == 'use_date':
                    res[prop_line.name.name] = {'value': lots_ids and '-'.join(['%s:%s' % (x.name, x.use_date) for x in lot_ids]) or '', 'attrs': False, 'image': False}
                elif lot_ids and prop_line.name.type_fields == 'gs1':
                    res[prop_line.name.name] = {'value': lots_ids and '-'.join([x.gs1 for x in lot_ids]) or '', 'attrs': False, 'image': False}
                elif prop_line.name.type_fields == 'pricelist':
                    prop_line.type_field_model = line._name
                    prop_line.model_obj_id = line.id
                    prop_line.type_field_ttype = 'many2one'
                    prop_line.type_field_name = 'pricelist_id'
                    res[prop_line.name.name] = {'value': prop_line.type_display, 'attrs': prop_line.type_display_attrs,
                                                'image': prop_line.image_small}
                else:
                    res[prop_line.name.name] = {'value': prop_line.type_display, 'attrs': prop_line.type_display_attrs, 'image': prop_line.image_small}
        for k, v in res.items():
            if v['value']:
                ret.append({'label': k, 'value': v})
        #_logger.info("RETURN %s" % ret)
        return ret

    @api.model
    def create(self, vals):
        if vals.get('type_url'):
            vals['type_url'] = self._clean_website(vals['type_url'])
        return super(ProductPropertiesType, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('type_url'):
            vals['type_url'] = self._clean_website(vals['type_url'])
        return super(ProductPropertiesType, self).write(vals)


class ProductPropertiesUom(models.Model):
    _name = "product.properties.uom"
    _description = "The properties units"
    _corder = "name_id, sequence"

    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    name = fields.Char('UOM Name', required=True, index=True)
    name_id = fields.Many2one("product.properties.type", string="Property name", required=True)


class ProductPropertiesUom(models.Model):
    _name = "product.properties.dropdown"
    _description = "The properties dropdown"
    _corder = "name_id, sequence, code"

    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    name = fields.Char('Name', required=True, index=True, translate=True)
    code = fields.Char('code')
    name_id = fields.Many2one("product.properties.type", string="Property name", required=True)

    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for dropdown in self:
            if dropdown.code:
                name = "[%s] %s" % (dropdown.code, dropdown.name)
            else:
                name = dropdown.name
            result.append((dropdown.id, name))
        return result


class ProductPropertiesPackage(models.Model):
    _name = "product.properties.package"
    _description = "The properteis packages/corpuses"

    name = fields.Char('Package Name', required=True, index=True, translate=True)
    name_id = fields.Many2one("product.properties.type", string="Property name", required=True)

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
