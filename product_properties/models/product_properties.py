# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from urllib.parse import urlparse

from odoo import api, fields, models, _, Command
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


def _clean_website(website):
    url = urlparse(website)
    if not url.scheme:
        if not url.netloc:
            url = url._replace(netloc=url.path, path='')
        website = url._replace(scheme='https').geturl()
    return website


MAGIC_FIELDS = ['id',
                'create_uid',
                'create_date',
                'write_date',
                'write_uid',
                '__last_update', ]

TYPES = [('char', 'String'),
         ('float', 'Float'),
         ('int', 'Integer'),
         ('currency', 'Currency'),
         ('date', 'Date'),
         ('range', 'Range'),
         ('boolean', 'Yes/No'),
         ('package', 'Package'),
         ('eval', 'HTML Eval filled'),
         ('dropdown_id', 'Dropdown menu'),
         ('pricelist', 'Linked width Price List'),
         ('url', 'Base on URL'),
         ('field', 'Base on field'),
         ('lot', 'Base on LOT/SN'),
         ('use_date', 'Base on Use date'),
         ('gs1', 'Base on GS1(UDI)'),
         ]


class ProductProperties(models.Model):
    _name = "product.properties"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Product properties"
    _order = "sequence, id"

    def _display_type_range(self):
        for record in self:
            record.type_range = "-".join([str(record.type_int), str(record.type_int_second)])

    def _display_type_package(self):
        for record in self:
            record.type_package = record.type_package_id and record.type_package_id.name or ''

    def _display_type_inverse(self):
        for record in self:
            if record.name.type_fields == 'dropdown_id':
                if record.type_dropdown_id:
                    record.type_dropdown_id = [(1, record.type_dropdown_id.id, {'name': record.type_display})]
                else:
                    record.type_dropdown_id = [(0, False, {'name': record.type_display})]
            elif record.name and "type_%s" % record.type_fields in self._fields:
                if record.type_field == 'float' and record.type_display == '':
                    record.type_display = '0'
                setattr(record, "type_%s" % record.type_fields, record.type_display)

    def _display_type(self):
        if self._context.get('block'):
            return False
        for record in self:
            if record.name.type_fields == 'dropdown_id':
                record.type_display = record.type_dropdown_id and record.type_dropdown_id.name_get()[0][1] or ''
            elif record.name.type_fields == 'eval':
                source = "%s" % getattr(record, "type_%s" % record.type_fields)
                model = self._context.get('force_model') or record
                try:
                    source = safe_eval(source, {'object': model, 'context': self._context})
                except Exception as e:
                    _logger.warning("The field eval not supported this syntax's error %s" % e)
                    source = ''
                record.type_display = source
            elif record.name and "type_%s" % record.type_fields in self._fields:
                record.type_display = "%s %s" % (getattr(record, "type_%s" % record.type_fields) or '',
                                                 record.type_uom_id and record.type_uom_id.name or '')
                if (self._context.get('force_display')
                        and self._context['force_display']
                        and getattr(record, "type_%s" % record.type_fields) in [False, '', ' ']):
                    record.type_display = False
            else:
                record.type_display = ''

            if record.name.type_fields == 'package':
                record.type_display_attrs = "x".join(
                    [str(record.dimensions_x), str(record.dimensions_y), str(record.dimensions_z)])
            else:
                record.type_display_attrs = ''

            # if record.name.type_fields == 'field' and not record.product_id:
            #     record.type_display = record.type_field_target.field_description

            if self._context.get('force_display') and self._context['force_display'] \
                and record.type_display in ['', ' ']:
                record.type_display = False

    active = fields.Boolean(
        'Active', default=True,
        help="If unchecked, it will allow you to hide the product properties without removing it.")

    product_tmpl_id = fields.Many2one(
        'product.template',
        'Product Template',
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        'Product',
        index=True
    )

    sequence = fields.Integer("Sequence", default=1, index=True, help="The first in the sequence is the default one.")

    name = fields.Many2one("product.properties.type", string="Property name", required=True)
    type_fields = fields.Selection(related="name.type_fields", string="Type properties", required=True, store=True)

    categ_id = fields.Many2one('product.properties.category', string='Category Properties', index=True)

    type_float = fields.Float(string="Value for Float")
    type_char = fields.Char(string="Value for Char")
    type_int = fields.Integer(string="Value for Int")
    type_int_second = fields.Integer("Value for Second Int")
    type_eval = fields.Text(string="Value for Eval")
    type_currency = fields.Monetary(string="Value for Currency", currency_field="currency_id")
    type_date = fields.Date(string="Value for Date")
    type_range = fields.Char("Value Range", compute='_display_type_range')
    type_boolean = fields.Boolean("Value for Boolean")
    type_url = fields.Char(string="URL")
    type_field = fields.Char(string="Field", compute="_get_type_field")
    type_field_name = fields.Char(string="Field name",
                                  compute="_get_type_field_properties",
                                  inverse="_set_type_field_name")
    type_field_ttype = fields.Char(string="Field type",
                                   compute="_get_type_field_properties",
                                   inverse="_set_type_field_ttype")
    type_field_model = fields.Char(string="Field model",
                                   compute="_get_type_field_properties",
                                   inverse="_set_type_field_model")
    model_obj_id = fields.Integer(string='Model object holder id',
                                  compute="_get_type_field_properties",
                                  inverse="_set_model_obj_id")

    type_field_model_id = fields.Many2one('ir.model',
                                          string='Target/Source Odoo model',
                                          domain=lambda self:
                                          self.env['product.properties.type']._get_domain_type_field_model_id())
    type_field_target = fields.Many2one('ir.model.fields',
                                        string='Target/Source Odoo field',
                                        help="Choice target/source field for collection data. "
                                             "target/source in odoo model.")

    type_package_id = fields.Many2one("product.properties.package", string="Value for Package")
    type_package = fields.Char("Type package", compute='_display_type_package')
    dimensions_x = fields.Float(string="X Dimensions")
    dimensions_y = fields.Float(string="Y Dimensions")
    dimensions_z = fields.Float(string="Z Dimensions")

    type_uom_id = fields.Many2one("product.properties.uom",
                                  string="UOM Name",
                                  ondelete="restrict")
    type_dropdown_id = fields.Many2one("product.properties.dropdown",
                                       string="Dropdown")
    type_display = fields.Char("Value",
                               compute='_display_type',
                               inverse='_display_type_inverse')
    type_display_attrs = fields.Char("Value attrs", compute='_display_type')
    currency_id = fields.Many2one('res.currency',
                                  string='Currency of properties',
                                  default=lambda self: self.env.user.company_id.currency_id)

    @api.model
    def ignore_fields(self):
        return ['__last_update', 'write_date', 'write_uid', 'create_date', 'create_uid', 'id', 'display_name',
                'sequence', 'company_id', 'name', 'model_obj_id', 'type_field_model_id', 'type_field_target',
                'type_field', 'type_field_name', 'type_field_ttype', 'type_field_model', 'currency_id']

    @api.model
    def product_property_fields(self):
        return list(filter(lambda r: r not in self.ignore_fields(), self._fields))

    def _get_model_obj_id(self):
        if self.type_field_model == 'product.product':
            model_obj_id = self.product_id.id
        elif self.type_field_model == 'product.template':
            model_obj_id = self.product_tmpl_id.id
        else:
            model_obj_id = False
        return model_obj_id

    # if not rec.model_obj_id and rec.type_field_model == 'product.product':
    #     rec.model_obj_id = rec.product_id.id
    # elif not rec.model_obj_id and rec.type_field_model == 'product.template':
    #     rec.model_obj_id = rec.product_tmpl_id.id

    def _get_type_field_properties(self):
        for field_name in self:
            if not field_name.type_field_name:
                field_name.type_field_name = field_name.type_field_target.name
            if not field_name.type_field_ttype:
                field_name.type_field_ttype = field_name.type_field_target.ttype
            if not field_name.type_field_model:
                field_name.type_field_model = field_name.type_field_target.model_id.model
            if not field_name.model_obj_id:
                field_name.model_obj_id = field_name._get_model_obj_id()
            # if not field_name.model_obj_id and field_name.type_field_model == 'product.product':
            #     field_name.model_obj_id = field_name.product_id.id
            # elif not field_name.model_obj_id and field_name.type_field_model == 'product.template':
            #     field_name.model_obj_id = field_name.product_tmpl_id.id

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
            if not rec.model_obj_id:
                rec.model_obj_id = rec._get_model_obj_id()
            # if not rec.model_obj_id and rec.type_field_model == 'product.product':
            #     rec.model_obj_id = rec.product_id.id
            # elif not rec.model_obj_id and rec.type_field_model == 'product.template':
            #     rec.model_obj_id = rec.product_tmpl_id.id

    def _get_type_field(self):
        for field_value in self:
            if field_value.type_field_target:
                model_obj = field_value.type_field_model
                ttype = field_value.type_field_ttype
                name = field_value.type_field_name
                field_id = field_value.model_obj_id
                if not field_id:
                    field_id = field_value.name.id
                    model_obj = 'product.properties.type'
                    ttype = 'char'
                    name = 'name'
                model = self.env[model_obj].with_context(**dict(self._context, display_default_code=False)).\
                    browse(field_id)
                if ttype == 'char':
                    if model._name == 'product.product' and name in ['name', 'display_name']:
                        name = model.is_product_variant and 'display_name' or 'name'
                    field_value.type_field = getattr(model, name)
                if ttype == 'text':
                    field_value.type_field = getattr(model, name)
                if ttype == 'html':
                    field_value.type_field = getattr(model, name)
                elif ttype == 'float':
                    field_value.type_field = "%d" % getattr(model, name)
                elif ttype == 'monetary':
                    field_value.type_field = "%d" % getattr(model, name)
                elif ttype == 'many2one':
                    field = getattr(model, name)
                    relation = field_value.type_field_target.relation
                    model = self.env[relation].with_context(**dict(self._context, display_default_code=False)).\
                        browse([field.id])
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

    @api.model
    def get_print_ids(self, print_ids, res, lines, mode=None):
        return False

    @api.model
    def _set_all_print_properties(self, res, default_res_model_id=False):
        if res._name == 'stock.picking':
            res_model_id = 'picking_id'
        elif res._name == 'sale.order':
            res_model_id = 'sale_id'
        elif res._name == 'account.move':
            res_model_id = 'invoice_id'
        elif res._name == 'res.partner':
            res_model_id = 'partner_id'
        elif res._name == 'purchase.order':
            res_model_id = 'purchase_id'
        else:
            res_model_id = False

        if default_res_model_id:
            res_model_id = default_res_model_id
        return res_model_id

    @api.model
    def set_products_print_properties(self, res, lines, default_res_model_id=False):
        return self.set_all_print_properties(res, lines, mode=['standard'], default_res_model_id=default_res_model_id)

    @api.model
    def set_all_print_properties(self, res, lines, mode=None, default_res_model_id=False):
        if mode is None:
            mode = ['standard']

        def add_exluded(x, ids):
            ids.update([x])
            return x

        mode = self._context.get('mode_print_properties') and self._context['mode_print_properties'] or mode
        # _logger.info("MODE %s:%s:%s" % (self._context, mode, 'partner_id' in res._fields))

        res_model_id = self._set_all_print_properties(res, default_res_model_id=default_res_model_id)
        if not res_model_id:
            return False

        for record in res:
            static_properties_obj = self.env['product.properties.static']
            print_properties = []
            ids = set([])
            print_ids = self.get_print_ids(False, res, lines, mode)
            partner_print_ids = False
            default_print_ids = False
            print_static_ids = False

            if res.invoice_sub_type:
                print_properties.append(Command.create({
                    'invoice_sub_type': res.invoice_sub_type.id,
                    'print': True,
                }))
            if 'category' in mode and 'category_print_properties' in res._fields:
                print_static_ids = [x.static_field for x in record.category_print_properties.mapped('type_ids') if
                                    not x.type_id and x.static_field]
                default_print_ids = [x for x in record.category_print_properties.mapped('type_ids') if
                                     x.type_id and not x.static_field]
                true_fields = self.env['product.properties.static']._set_static_ignore_print_properties()
                for line in record.category_print_properties.mapped('type_ids').filtered(
                        lambda x: not x.type_id and x.static_field in true_fields):
                    setattr(record.category_print_properties, line.static_field, getattr(line, line.static_field))
            if 'partner' in mode and 'partner_id' in res._fields:
                true_fields = self.env['product.properties.static']._set_static_ignore_print_properties()
                for field in true_fields:
                    if field in record.partner_id._fields and field in res._fields:
                        value = getattr(record.partner_id, field)
                        setattr(res, field, value)
                partner_print_ids = [x for x in record.partner_id.print_properties if x.print]
                # _logger.info("PARTNER %s:%s" % (partner_print_ids, record.partner_id))
            if 'standard' in mode:
                print_static_ids = filter(lambda r: r not in static_properties_obj.ignore_fields(),
                                          static_properties_obj._fields)
                for r in lines.mapped('product_id'):
                    if not print_ids:
                        print_ids = r.product_properties_ids | r.tmpl_product_properties_ids
                    else:
                        print_ids |= r.product_properties_ids | r.tmpl_product_properties_ids
            if (
                    print_ids or print_static_ids or partner_print_ids or default_print_ids) and not record.print_properties:
                if default_print_ids:
                    print_properties += [Command.create({
                        'name': add_exluded(x.type_id.id, ids),
                        res_model_id: res.id,
                        'print': True,
                        'sequence': x.sequence
                    }) for x in default_print_ids if x.type_id and x.type_id.id not in list(ids)]
                if partner_print_ids:
                    print_properties += [Command.create({
                        'name': add_exluded(x.name.id, ids),
                        res_model_id: res.id,
                        'print': True,
                        'sequence': x.sequence
                    }) for x in partner_print_ids if x.name and x.name.id not in list(ids) and not x.static_field]
                    print_properties += [Command.create({
                        'static_field': x.static_field,
                        res_model_id: res.id,
                        'print': True,
                        'sequence': 9999
                    }) for x in partner_print_ids if not x.name and x.static_field and x.static_field not in static_properties_obj.ignore_fields()]
                if print_ids:
                    print_properties += [Command.create({
                        'name': add_exluded(x.name.id, ids),
                        res_model_id: res.id,
                        'print': True,
                        'sequence': x.sequence
                    }) for x in print_ids if x.name and x.name.id not in list(ids)]
                if print_static_ids:
                    print_properties += [Command.create({
                        'static_field': x,
                        res_model_id: res.id,
                        'print': True,
                        'sequence': 9999}) for x in print_static_ids]
                # _logger.info("LIST %s:%s:%s:%s" % (self._context.get('mode_print_properties'), lines.mapped('product_id'), print_properties, ids))
            return print_properties
        return False

    def _get_default_product_properties_ids(self, categ_ids, product, default=False):
        if not default:
            default = {}
        default_values = {}
        model = product._name
        properties = categ_ids.mapped('lines_ids')
        res = []
        sequence = 0
        name_ids = [x.name.id for x in product.product_properties_ids]
        for rec in properties.sorted(key=lambda r: r.sequence):
            rec = rec.name
            if 'categ_id' in rec._fields and default.get(rec.categ_id):
                default_values = default[rec.categ_id]
            sequence += 1
            if rec.id not in name_ids:
                value = {'product_id': model == 'product.product' and product.id or False,
                         'product_tmpl_id': 'product_tmpl_id' in product._fields and product.product_tmpl_id.id or False,
                         'sequence': sequence,
                         'name': rec.id,
                         'type_fields': rec.type_fields,
                         'type_char': default_values.get('type_char') or rec.type_char,
                         'type_int': default_values.get('type_int') or rec.type_int,
                         'type_int_second': rec.type_int_second,
                         'type_float': default_values.get('type_float') or rec.type_float,
                         'type_boolean': rec.type_boolean,
                         'type_package_id': rec.type_package_id and rec.type_package_id.id or False,
                         'type_field_model_id': rec.type_field_model_id and rec.type_field_model_id.id or False,
                         'type_field_target': rec.type_field_target and rec.type_field_target.id or False,
                         'type_dropdown_id': default_values.get('type_dropdown_id')
                                                or rec.type_dropdown_id
                                                and rec.type_dropdown_id.id or False,
                         'dimensions_x': rec.dimensions_x,
                         'dimensions_y': rec.dimensions_y,
                         'dimensions_z': rec.dimensions_z,
                         'type_uom_id': rec.type_uom_id and rec.type_uom_id.id or False,
                         'currency_id': self.env.user.company_id.currency_id.id,
                         }
                res.append(Command.create(value))
        return res

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
        self.update({
            'image_1920': self.type_package_id.image_1920,
            'dimensions_x': self.type_package_id.dimensions_x,
            'dimensions_y': self.type_package_id.dimensions_y,
            'dimensions_z': self.type_package_id.dimensions_z,
        })

    def _sanitize_vals(self, vals):
        if vals.get('type_url', False):
            vals['type_url'] = _clean_website(vals['type_url'])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sanitize_vals(vals)
            if vals.get('name'):
                # check for default values
                name = self.env['product.properties.type'].browse(vals['name'])
                for field_name in self.product_property_fields():
                    if not vals.get(field_name, False) and field_name in name._fields:
                        vals[field_name] = getattr(name, field_name)
        return super().create(vals_list)

    def write(self, vals):
        self._sanitize_vals(vals)
        return super(ProductProperties, self).write(vals)


class ProductPropertiesUom(models.Model):
    _name = "product.properties.uom"
    _description = "The properties units"
    _order = "name_id, sequence"

    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    name = fields.Char('UOM Name', required=True, index=True)
    name_id = fields.Many2one("product.properties.type", string="Property name", required=True)


class ProductPropertiesDropdown(models.Model):
    _name = "product.properties.dropdown"
    _description = "The properties dropdown"
    _order = "name_id, sequence, code"

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
    _inherit = ['image.mixin']
    _description = "The properties packages/corpora"

    name = fields.Char('Package Name', required=True, index=True, translate=True)
    name_id = fields.Many2one("product.properties.type", string="Property name", required=True)

    dimensions_x = fields.Float("X Dimensions")
    dimensions_y = fields.Float("Y Dimensions")
    dimensions_z = fields.Float("Z Dimensions")
