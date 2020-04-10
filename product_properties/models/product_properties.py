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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from lxml import etree
from lxml.builder import E

import logging

_logger = logging.getLogger(__name__)

TYPES = [('char', _('String')),
         ('float', _('Float')),
         ('int', _('Integer')),
         ('currency', _('Currency')),
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


def name_boolean_print(id):
    return 'print_' + str(id)


def is_boolean_print(name):
    return name.startswith('print_')


def is_reified_print(name):
    return is_boolean_print(name)


def get_boolean_print(name):
    return int(name[6:])


class ProductPropertiesPrint(models.Model):
    _name = "product.properties.print"
    _description = "Product properties for printing"
    _order = "system_properties, sequence"

    def _get_field_name_filter(self):
        static_properties_obj = self.env['product.properties.static']
        ret = []
        for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields):
            field = static_properties_obj.fields_get(g)[g]
            ret.append((g, field['string']))
        return ret

    name = fields.Many2one("product.properties.type", string="Property name",  translate=True)
    print = fields.Boolean('Print')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'product.properties.print'))
    categ_id = fields.Many2one("product.properties.category", "Category", index=True)

    partner_id = fields.Many2one('res.partner', string='Partner', index=True)
    order_id = fields.Many2one("sale.order", string="Sale order", index=True)
    invoice_id = fields.Many2one("account.invoice", string="Invoice", index=True)
    picking_id = fields.Many2one("stock.picking", string="Transfer Reference", index=True)
    system_properties = fields.Boolean('System used')
    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    static_field = fields.Selection(selection="_get_field_name_filter", string="Static Properties Field name")

    def get_print_properties(self):
        return [x.name.id for x in self if not x.static_field and x.print]

    def get_print_static_properties(self):
        return [x.static_field for x in self if x.static_field and x.print]

    @api.multi
    def unlink(self):
        for properties in self:
            if properties.system_properties:
                raise UserError(_('You cannot delete system properties.'))
        return super(ProductPropertiesPrint, self).unlink()

#    @api.model
#    def fields_get(self, allfields=None, attributes=None):
#        res = super(ProductPropertiesPrint, self).fields_get(allfields, attributes=attributes)
#        static_properties_obj = self.env['product.properties.static']
#        dinamic_properties_obj = self.env['product.properties.category']
        # boolean group fields
#        for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj.with_context(lang="en")._fields):
#            field = static_properties_obj.fields_get(g)[g]
#            res['print_' + g.lower().replace(" ", "_")] = {
#                'type': 'boolean',
#                'string': field["string"],
#                'compute': "_get_print_field",
#                'exportable': False,
#                'selectable': False,
#            }
#        for categ in dinamic_properties_obj.search([]):
#            for line in categ.lines_ids:
#                for g in line.with_context(lang="en"):
#                    res['print_' + g.name.name.lower().replace(" ", "_")+"_%d" % g.name.id] = {
#                        'type': 'boolean',
#                        'string': g.name.name,
#                        'compute': "_get_print_field",
#                        'exportable': False,
#                        'selectable': False,
#                    }
        #_logger.info("FIELDS %s" % res)
#        return res

    @api.multi
    def _get_print_field(self):
        fields = []
        static_properties_obj = self.env['product.properties.static']
        dinamic_properties_obj = self.env['product.properties.category']
        for categ in dinamic_properties_obj.search([]):
            for line in categ.lines_ids:
                for g in line.with_context(lang="en"):
                    fields.append('print_' + g.name.name.lower().replace(" ", "_")+"_%d" % g.name.id)
        for record in self:
            for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj.with_context(lang="en")._fields):
                setattr(self, 'print_' + g.lower().replace(" ", "_"), record.print)
            for field in fields:
                parts = field.split("_")
                if record.name == parts[1] and  record.name.id == int(parts[2]):
                    setattr(self, field, record.print)

    @api.model
    def _properties_print_view(self, view=False):
        """ Modify the view with xmlid ``product_properties.sale_order_print_view``, which inherits
            the user form view, and introduces the reified group fields.
        """
        if self._context.get('install_mode'):
            # use installation/admin language for translatable names in the view
            user_context = self.env['res.users'].context_get()
            self = self.with_context(**user_context)

        # We have to try-catch this, because at first init the view does not
        # exist but we are already creating some basic groups.
        if not view:
            view = self.env.ref('product_properties.sale_order_print_view', raise_if_not_found=False)
        if view and view.exists() and view._name == 'ir.ui.view':
            static_properties_obj = self.env['product.properties.static']
            dinamic_properties_obj = self.env['product.properties.category']
            attrs = {}
            attrs['groups'] = 'product_properties.group_properties_print'
            # group_properties_print = view.env.ref('product_properties.group_properties_print')
            xml0, xml1, xml2 = [], [], []
            #xml0.append(E.xpath(expr="//notebook/page[@name='print_properties']", position="inside"))
            xml1.append(E.separator(string=_('Print Properties'), colspan="2"))
            for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields):
                field = static_properties_obj.fields_get(g)[g]
                field_name = "print_" + g.lower().replace(" ", "_")
                xml2.append(E.field(name=field_name, **attrs))
            for categ in dinamic_properties_obj.search([]):
                for line in categ.lines_ids:
                    for g in line.with_context(lang="en"):
                        field_name = 'print_' + g.name.name.lower().replace(" ", "_")+"_%d" % g.name.id
                        xml2.append(E.field(name=field_name, **attrs))
            xml2.append({'class': "o_label_nowrap"})
            xml0.append(E.field(name="print_properties", groups="product_properties.group_properties_print"))
            xml = E.xpath(*(xml0), E.group(*(xml1), col="2"), E.group(*(xml2), col="4"), expr="//notebook/page[@name='print_properties']", position="inside")
            xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY PRODUCT PROPERTIES"))
            xml_content = etree.tostring(xml, pretty_print=True, encoding="unicode")
            _logger.info("XML %s" % xml_content)

            if not view.check_access_rights('write', raise_exception=False):
                # erp manager has the rights to update groups/users but not
               # to modify ir.ui.view
                if self.env.user.has_group('base.group_erp_manager'):
                    view = view.sudo()

            new_context = dict(view._context)
            new_context.pop('install_mode_data', None)  # don't set arch_fs for this computed view
            new_context['lang'] = None
            view.with_context(new_context).write({'arch': xml_content})
        return False


class ProductPropertiesStatic(models.Model):
    _name = "product.properties.static"
    _description = "Product static properties"
    _order = "sequence, id"

    @api.multi
    def _links_get(self):
        link_obj = self.env['res.request.link']
        return [(r.object, r.name) for r in link_obj.search([])]

    sequence = fields.Integer("Sequence", default=9999, index=True, help="The first in the sequence is the default one.")
    object_id = fields.Reference(string='Reference', selection=_links_get, readonly=True, ondelete="set null")
    invoice_sub_type = fields.Many2one("product.properties.static.dropdown", string="Type Documets",
                                domain="[('field_name', '=', 'invoice_sub_type')]")
    currency_id = fields.Many2one('res.currency', string='Currency of properties', default=lambda self: self.env.user.company_id.currency_id)

    @api.multi
    def _display_type(self):
        if self._context.get('block'):
            return False

    @api.model
    def ignore_fields(self):
        return ['__last_update', 'write_date', 'write_uid', 'create_date', 'create_uid', 'id', 'display_name',
                'sequence', 'company_id', 'name', 'object_id', 'currency_id']

    @api.model
    def static_property_data(self, res, vals, updates=False):
        property_data = False
        if "invoice_sub_type" in vals:
            property_data = {
                'invoice_sub_type': vals.get('invoice_sub_type') and vals['invoice_sub_type'] or False,
            }
            if vals.get('invoice_sub_type'):
                del vals['invoice_sub_type']
        if property_data:
            line_property_data = self.new(property_data)
            property_data_id = self.create(line_property_data._convert_to_write(line_property_data._cache))
            res.write({'product_prop_static_id': property_data_id.id})
            res.product_prop_static_id.update({'object_id': "%s,%d" % ("%s" % res._name, res.id)})
        if updates:
            vals.update(updates)
        return vals

#class ProductPropertiesStaticPrint(models.Model):
#    _name = "product.properties.static.print"

#    sequence = fields.Integer("Sequence", default=1, index=True, help="The first in the sequence is the default one.")


class ProductProperties(models.Model):
    _name = "product.properties"
    _description = "Product properties"
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
        if self._context.get('block'):
            return False
        for record in self:
            if record.name.type_fields == 'dropdown_id':
                record.type_display = record.type_dropdown_id and record.type_dropdown_id.name_get()[0][1] or ''
            elif record.name and "type_%s" % record.type_fields in self._fields:
                record.type_display = "%s %s" % (getattr(record, "type_%s" % record.type_fields) or '',
                                                 record.type_uom_id and record.type_uom_id.name or '')
                if self._context.get('force_display') and self._context['force_display'] and getattr(record,
                                                                                                     "type_%s" % record.type_fields) in [False, '', ' ']:
                    record.type_display = False
            else:
                record.type_display = ''
            if record.name.type_fields == 'package':
                record.type_display_attrs = "x".join(
                    [str(record.dimensions_x), str(record.dimensions_y), str(record.dimensions_z)])
            else:
                record.type_display_attrs = ''
            if record.name.type_fields == 'field' and record.product_id == False:
                record.type_display = record.type_field_target.field_description
            if self._context.get('force_display') and self._context['force_display'] and record.type_display in ['',
                                                                                                                 ' ']:
                record.type_display = False
            # _logger.info("TYPE %s=%s" % (record.name.name,record.type_display))

    def _get_type_field_model_id(self):
        return json.dumps(self.env['product.properties.type']._get_type_field_model_id())

    product_tmpl_id = fields.Many2one('product.template', 'Product Template', index=True)
    product_id = fields.Many2one('product.product', 'Product', index=True)

    sequence = fields.Integer("Sequence", default=1, index=True, help="The first in the sequence is the default one.")

    name = fields.Many2one("product.properties.type", string="Property name", required=True, translate=True)
    type_fields = fields.Selection(related="name.type_fields", string="Type properties", required=True, store=True)

    categ_id = fields.Many2one('product.properties.category', string='Category Properties', index=True)

    type_float = fields.Float(string="Value for Float")
    type_char = fields.Char(string="Value for Char")
    type_int = fields.Integer(string="Value for Int")
    type_int_second = fields.Integer("Value for Second Int")
    type_currency = fields.Monetary(string="Value for Currency", currency_field="currency_id")
    type_date = fields.Date(string="Value for Date")
    type_range = fields.Char("Value Range", compute='_display_type_range')
    type_boolean = fields.Boolean("Value for Boolean")
    type_url = fields.Char(help="URL")
    type_field = fields.Char(help="Field", compute="_get_type_field")
    type_field_name = fields.Char(help="Field", compute="_get_type_field_properties", inverse="_set_type_field_name")
    type_field_ttype = fields.Char(help="Field", compute="_get_type_field_properties", inverse="_set_type_field_ttype")
    type_field_model = fields.Char(help="Field", compute="_get_type_field_properties", inverse="_set_type_field_model")
    model_obj_id = fields.Integer('Model object holder id', compute="_get_type_field_properties",
                                  inverse="_set_model_obj_id")

    type_field_model_id = fields.Many2one('ir.model', string='Target/Source Odoo model',
                                          domain=_get_type_field_model_id)
    type_field_target = fields.Many2one('ir.model.fields', string='Target/Source Odoo field',
                                        help="""Choice target/source field for collection data.
                                  target/source in odoo model.""",
                                        domain="[('model_id', '=', type_field_model_id), ('ttype', 'in', ['char', 'monetary', 'float', 'many2one']), ('name', 'not in', ('id', 'create_uid','create_date', 'write_date', 'write_uid', '__last_update', 'lines'))]")

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
    currency_id = fields.Many2one('res.currency', string='Currency of properties', default=lambda self: self.env.user.company_id.currency_id)

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
            #elif not field_name.model_obj_id and field_name.type_field_model == 'product.pricelist.item':
            #   field_name.model_obj_id = field_name.pricelist_rule_id.id

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
                model = self.env[model_obj].with_context(self._context, display_default_code=False).browse(id)
                if ttype == 'char':
                    if model._name == 'product.product' and name in ['name', 'display_name']:
                        # display only the attributes with multiple possible values on the template
                        variable_attributes = model.attribute_line_ids.filtered(
                            lambda l: len(l.value_ids) > 1).mapped('attribute_id')
                        variant = model.attribute_value_ids._variant_name(variable_attributes)
                        field_value.type_field = variant and "%s (%s)" % (model.name, variant) or model.name
                    else:
                        field_value.type_field = getattr(model, name)
                elif ttype == 'float':
                    field_value.type_field = "%d" % getattr(model, name)
                elif ttype == 'monetary':
                    field_value.type_field = "%d" % getattr(model, name)
                elif ttype == 'many2one':
                    field = getattr(model, name)
                    relation = field_value.type_field_target.relation
                    model = self.env[relation].with_context(self._context, display_default_code=False).browse(
                        [field.id])
                    if 'display_name' in model._fields:
                        # _logger.info("FIELDS %s" % model._fields)
                        field_value.type_field = getattr(model, 'display_name')
                    else:
                        if model._name == 'product.product':
                            # display only the attributes with multiple possible values on the template
                            variable_attributes = model.attribute_line_ids.filtered(
                                lambda l: len(l.value_ids) > 1).mapped('attribute_id')
                            variant = model.attribute_value_ids._variant_name(variable_attributes)
                            field_value.type_field = variant and "%s (%s)" % (model.name, variant) or model.name
                        else:
                            field_value.type_field = getattr(model, 'name')
                if field_value.type_field in [0, '', ' ']:
                    field_value.type_field = False
            else:
                field_value.type_field = False

    @api.onchange('name')
    def _onchange_name(self):
        if self.name.type_fields == 'field':
            self.type_field_model_id = self.name.type_field_model_id.id
            self.type_field_target = self.name.type_field_target.id
        elif self.name.type_fields == 'currency' and self.type_currency == 0.0:
            self.type_currency = self.type_float
            self.type_float = 0.0
        elif self.name.type_fields == 'float' and self.type_float == 0.0:
            self.type_float = self.type_currency
            self.type_currency = 0.0
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
        return {'value': {'image': self.type_package_id.image, 'image_medium': self.type_package_id.image_medium,
                          'image_small': self.type_package_id.image_small,
                          'dimensionproduct.properties.prints_x': self.type_package_id.dimensions_x,
                          'dimensions_y': self.type_package_id.dimensions_y,
                          'dimensions_z': self.type_package_id.dimensions_z}}

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
    _description = "Category Product properties"

    name = fields.Char('Property name', required=True, translate=True)
    applicability = fields.Selection([
        ('product', 'Product'),
        ('template', 'Product template(o2m)'),
        ('templateoo', 'Product template(o2o)')], required=True)
    lines_ids = fields.One2many(comodel_name='product.properties.category.lines',
                                inverse_name="categ_id",
                                string='Category properties', ondelete='restrict')
    print_ids = fields.One2many('product.properties.print', 'categ_id', string='Category print properties')
    # properties_ids = fields.Many2many('product.properties', relation='product_properties_cat', column1='categ_id', column2='properties_id', string='Product Properties')


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
                record.type_display = "%s %s" % (
                record["type_%s" % record.type_fields] or '', record.type_uom_id and record.type_uom_id.name or '')
            else:
                record.type_display = ''
            if record.name.type_fields == 'package':
                record.type_display_attrs = "x".join(
                    [str(record.dimensions_x), str(record.dimensions_y), str(record.dimensions_z)])
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
    type_int = fields.Integer(related="name.type_int", string="Value for Int", store=True)
    type_int_second = fields.Integer(related="name.type_int_second", string="Value for Second Int")
    type_currency = fields.Monetary(string="Value for Currency", currency_field="currency_id")

    type_date = fields.Date(string="Value for Date")
    type_range = fields.Char("Value Range", compute='_display_type_range')
    type_boolean = fields.Boolean(related="name.type_boolean", string="Value for Boolean")
    type_url = fields.Char(help="URL")
    type_field = fields.Char(help="Field", compute="_get_type_field")
    type_field_model_id = fields.Many2one('ir.model', string='Target/Source Odoo model',
                                          domain=_get_type_field_model_id)
    type_field_target = fields.Many2one('ir.model.fields', string='Target/Source Odoo field',
                                        help="""Choice target/source field for collection data.
                                  target/source in odoo model.""",
                                        domain="[('model_id', '=', type_field_model_id), ('ttype', 'in', ['char', 'monetary', 'float', 'many2one']), ('name', 'not in', ('id', 'create_uid','create_date', 'write_date', 'write_uid', '__last_update', 'lines'))]")
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
    currency_id = fields.Many2one('res.currency', string='Currency of properties', default=lambda self: self.env.user.company_id.currency_id)

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
    _order = "sequence, id"

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
    type_currency = fields.Monetary(string="Value for Currency", currency_field="currency_id")
    type_date = fields.Date(string="Value for Date")
    type_boolean = fields.Boolean("Value for Boolean")
    type_url = fields.Char(help="URL")
    type_field = fields.Char(help="Field", compute="_get_type_field")
    type_field_model_id = fields.Many2one('ir.model', string='Target/Source Odoo model',
                                          domain=_get_type_field_model_id)
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
    currency_id = fields.Many2one('res.currency', string='Currency of properties', default=lambda self: self.env.user.company_id.currency_id)

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

    def get_product_properties_break(self, row, br):
        return row % br

    def _get_defult_currency_id(self, properties, field_name):
        return properties.currency_id

    def get_product_properties_print(self, product, properties_print=False, line=False, lot_ids=False, description=False, codes=False):
        res = {}
        ret = []
        print_ids = []
        static_properties_obj = self.env['product.properties.static']
        if properties_print:
            print_ids = properties_print.get_print_properties()
            print_static_ids = properties_print.get_print_static_properties()
        if self._context.get('force_print'):
            print_static_ids = filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields)
        #else:
        #    print_static_ids = list(set(filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields)) - set(print_static_ids))
        if 'tproduct_properties_ids' not in product._fields and 'product_properties_ids' in product._fields:
            properties_available = (product.product_properties_ids)
        elif 'tproduct_properties_ids' in product._fields and 'product_properties_ids' not in product._fields:
            properties_available = (product.tproduct_properties_ids)
        elif 'tproduct_properties_ids' in product._fields and 'product_properties_ids' in product._fields:
            properties_available = (product.tproduct_properties_ids, product.product_properties_ids)
        else:
            properties_available = ()
        for properties in properties_available:
            if self._context.get('force_print'):
                print_ids = [x.name.id for x in properties]
            #else:
            #    print_ids = list(set([x.name.id for x in properties]) - set(print_ids))
            for prop_line in properties.sorted(key=lambda r: r.name.sequence):
                if properties_print and prop_line.name.id in print_ids:
                    if line and prop_line.type_field_name in line._fields:
                        prop_line.type_field_model = line._name
                        prop_line.model_obj_id = line.id
                    if lot_ids and not isinstance(lot_ids, pycompat.string_types) and prop_line.name.type_fields == 'lot':
                        res[prop_line.name.name] = {
                            'value': '-'.join(map(lambda lot: lot.lot_id and lot.lot_id.name or '', lot_ids)),
                            'attrs': False, 'image': False, 'sequence': prop_line.name.sequence,
                            'type': prop_line.name.type_fields,
                            'currency_id': self._get_defult_currency_id(prop_line, prop_line.name)}
                    elif lot_ids and not isinstance(lot_ids, pycompat.string_types) and prop_line.name.type_fields == 'use_date' and any([lot.id for lot in lot_ids if lot.lot_id and lot.lot_id.use_date]):
                        res[prop_line.name.name] = {'value': '-'.join(map(lambda lot: lot.lot_id.use_date and "%s" % fields.Date.from_string(lot.lot_id.use_date) or '', lot_ids)),
                                                    'attrs': False, 'image': False, 'sequence': prop_line.name.sequence,
                                                    'type': prop_line.name.type_fields,
                                                    'currency_id': self._get_defult_currency_id(prop_line, prop_line.name)}
                    elif lot_ids and not isinstance(lot_ids, pycompat.string_types) and prop_line.name.type_fields == 'gs1':
                        res[prop_line.name.name] = {
                            'value': '-'.join(map(lambda lot: lot.lot_id and lot.lot_id.hr_gs1 or '', lot_ids)),
                            'attrs': False, 'image': False,
                            'sequence': prop_line.name.sequence,
                            'type': prop_line.name.type_fields,
                            'currency_id': self._get_defult_currency_id(prop_line, prop_line.name.type_fields)}
                    elif lot_ids and isinstance(lot_ids, pycompat.string_types):
                        res[prop_line.name.name] = {'value': lot_ids and '-'.join([x for x in lot_ids]) or '',
                                                    'attrs': False, 'image': False, 'sequence': prop_line.name.sequence,
                                                    'type': prop_line.name.type_fields,
                                                    'currency_id': self._get_defult_currency_id(prop_line, prop_line.name)}
                    elif not line and codes and prop_line.name.type_fields == 'pricelist':
                        value = ", ".join(codes)
                        res[prop_line.name.name] = {'value': value,
                                                    'attrs': prop_line.with_context(
                                                        force_display=True).type_display_attrs,
                                                    'image': prop_line.image_small, 'sequence': prop_line.name.sequence,
                                                    'type': prop_line.name.type_fields,
                                                    'currency_id': self._get_defult_currency_id(prop_line, prop_line.name)}
                    elif line and prop_line.name.type_fields == 'pricelist':
                        prop_line.type_field_model = line._name
                        if codes:
                            value = ", ".join(codes)
                        elif not codes and 'code' in line._fields:
                            value = line.code
                        else:
                            prop_line.model_obj_id = line.id
                            prop_line.type_field_ttype = 'many2one'
                            prop_line.type_field_name = 'pricelist_rule_id'
                            value = prop_line.with_context(force_display=True).type_display
                        res[prop_line.name.name] = {'value': value,
                                                    'attrs': prop_line.with_context(
                                                        force_display=True).type_display_attrs,
                                                    'image': prop_line.image_small, 'sequence': prop_line.name.sequence,
                                                    'type': prop_line.name.type_fields,
                                                    'currency_id': self._get_defult_currency_id(prop_line, prop_line.name)}
                    else:
                        res[prop_line.name.name] = {'value': prop_line.with_context(force_display=True).type_display,
                                                    'attrs': prop_line.with_context(
                                                        force_display=True).type_display_attrs,
                                                    'image': prop_line.image_small, 'sequence': prop_line.name.sequence,
                                                    'type': prop_line.name.type_fields,
                                                    'currency_id': self._get_defult_currency_id(prop_line, prop_line.name)}

        for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields):
            if properties_print and g in print_static_ids:
                prop_line = product.product_prop_static_id
                if not prop_line:
                    continue
                field = static_properties_obj.fields_get(g)[g]
                field_value = getattr(prop_line, g)
                if not field_value:
                    continue
                #_logger.info("STATIC %s::%s:%s:%s" % (g,field_value,field,prop_line._fields))
                if field['type'] == 'many2one':
                    field_relation = field_value
                    field_name = 'id'
                    if 'name' in field_relation._fields:
                        field_name = 'name'
                    if 'display_name' in field_relation._fields:
                        field_name = 'display_name'
                    field_value = getattr(field_relation, field_name)
                res[field['string']] = {'value': field_value,
                                        'attrs': False,
                                        'image': False,
                                        'sequence': prop_line.sequence,
                                        'type': field['type'],
                                        'currency_id': self._get_defult_currency_id(prop_line, g)}
        for k, v in dict(sorted(res.items(), key=lambda x: x[1]['sequence'])).items():
            if v['value']:
                #_logger.info("K:V: %s:%s" % (k,v))
                ret.append({'label': k, 'value': v})
        return ret

    @api.model
    def create(self, vals):
        if vals.get('type_url'):
            vals['type_url'] = self._clean_website(vals['type_url'])
        #self.env['product.properties.print']._properties_print_view()
        #self.env['ir.actions.actions'].clear_caches()
        return super(ProductPropertiesType, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('type_url'):
            vals['type_url'] = self._clean_website(vals['type_url'])
        #self.env['product.properties.print']._properties_print_view()
        #self.env['ir.actions.actions'].clear_caches()
        return super(ProductPropertiesType, self).write(vals)


class ProductPropertiesUom(models.Model):
    _name = "product.properties.uom"
    _description = "The properties units"
    _corder = "name_id, sequence"

    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    name = fields.Char('UOM Name', required=True, index=True)
    name_id = fields.Many2one("product.properties.type", string="Property name", required=True)


class ProductPropertiesDropdown(models.Model):
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


class ProductPropertiesStaticDropdown(models.Model):
    _name = "product.properties.static.dropdown"
    _description = "The properties static dropdown"
    _corder = "name_id, sequence, code"

    def _get_field_name_filter(self):
        static_properties_obj = self.env['product.properties.static']
        ret = []
        for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields):
            field = static_properties_obj.fields_get(g)[g]
            ret.append((g, field['string']))
        return ret

    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    name = fields.Char('Name', required=True, index=True, translate=True)
    code = fields.Char('code')
    field_name = fields.Selection(selection="_get_field_name_filter", string="Filter")
    is_currency = fields.Boolean("Has currency")

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
