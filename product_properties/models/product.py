# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
import base64
from lxml import etree
from copy import deepcopy
import os
import json
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

from odoo.addons import decimal_precision as dp

from odoo.tools import float_compare, pycompat

import logging
_logger = logging.getLogger(__name__)

def name_boolean_print(id):
    return 'static_pp_' + str(id)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    count_datasheets = fields.Integer('Count Datasheets', compute='_compute_has_datasheets')
    datasheet_ids = fields.One2many('product.manufacturer.datasheets', compute="_compute_datasheet_ids")

    product_properties_has = fields.Boolean(compute="_compute_product_properties", string="Category Has Product properties")
    product_properties_ids = fields.One2many("product.properties", "product_id", string='Product properties')
    product_prop_static_id = fields.Many2one("product.properties.static", 'Static Product properties')
    tproduct_prop_static_id = fields.Many2one("product.properties.static", related="product_tmpl_id.product_prop_static_id")

    has_product_properties = fields.Boolean(compute="_compute_has_product_properties", string="Product has properties")
    tproduct_properties_ids = fields.Many2many("product.properties", compute="_compute_tproduct_properties_ids", string='Product template properties')

    categ_ids = fields.Many2many('product.properties.category', relation="product_prod_prop",
                                 string='Global Category properties', domain="[('applicability', '=', 'product')]")
    tcateg_ids = fields.Many2many('product.properties.category', relation="product_prod_prop",
                                 string='Global Category properties', domain="[('applicability', '=', 'template')]")
    curr_categ_ids = fields.Many2many('product.properties.category', string='Category properties', compute='_compute_curr_categ_ids')

    manufacturer = fields.Many2one('product.manufacturer', string="Product Manufacturer")
    manufacturer_pname = fields.Char(string='Manuf. Product Name', related="manufacturer.manufacturer_pname")
    manufacturer_pref = fields.Char(string='Manuf. Product Code', related='manufacturer.manufacturer_pref')
    manufacturer_purl = fields.Char(string='Manuf. Product URL', related='manufacturer.manufacturer_purl')

    manufacturer_id = fields.Many2one('res.partner', string='Manufacturer', compute="_compute_manufacturer", store=True)

    @api.multi
    def _compute_product_properties(self):
        for record in self:
            if record.product_tmpl_id.categ_id and record.product_tmpl_id.categ_id.product_properties_ids:
                record.product_properties_has = True
            else:
                record.product_properties_has = False

    @api.multi
    def _compute_tproduct_properties_ids(self):
        for record in self:
            if record.product_tmpl_id:
                record.tproduct_properties_ids = record.product_tmpl_id.product_properties_ids

    @api.multi
    def _compute_manufacturer(self):
        for record in self:
            if not record.manufacturer_id:
                record.manufacturer_id = record.product_tmpl_id.manufacturer_id

    @api.one
    @api.depends('product_properties_ids')
    def _compute_has_product_properties(self):
        self.has_product_properties = len(self.product_properties_ids.ids) > 0 or len(self.tproduct_properties_ids.ids) > 0

    @api.one
    def _compute_curr_categ_ids(self):
        ids = list(set(self.product_properties_ids.mapped('categ_id').mapped('id')))
        #_logger.info("USASGET %s" % ids)
        if ids:
            self.curr_categ_ids = [(4, id, False) for id in ids]
        else:
            self.curr_categ_ids = False

    @api.onchange('manufacturer_pname', 'manufacturer_pref', 'manufacturer_purl')
    def _onchange_manufacturer_data(self):
        if not self.manufacturer and self.product_tmpl_id.product_variant_count > 1:
            self.update({'manufacturer': [0, False, {'manufacturer': self.product_tmpl_id.manufacturer.id,
                                            'product_tmpl_id': self.product_tmpl_id.id, 'product_id': self.id,
                                            'manufacturer_pname': self.manufacturer_pname, 'manufacturer_pref': self.manufacturer_pref,
                                            'manufacturer_purl': self.manufacturer_purl}]})

    #@api.model
    #def fields_get(self, allfields=None, attributes=None):
    #    res = super(ProductProduct, self).fields_get(allfields, attributes=attributes)
    #    #field_obj = self.env['ir.model.fields']
    #    model_obj = self.env['product.properties.static']
    #    # boolean group fields
    #    for g in filter(lambda r: r[0] not in self.env['product.properties.static'].ignore_fields(), model_obj._fields):
    #        field_name = name_boolean_print(int.from_bytes(g.encode('utf-8'), 'little'))
    #        if allfields and field_name not in allfields:
    #            continue
    #        #field = field_obj.search([('name', '=', g), ('model_id', '=', model_obj.id)])
    #        res[field_name] = {
    #            'type': 'boolean',
    #            'related': 'product_prop_static_id.%s' % g,
    #            'exportable': False,
    #            'selectable': False,
    #        }
    #    #_logger.info("FIELDS %s" % res)
    #    return res

    #@api.model
    #def fields_view_get(self, view_id=None, view_type='form',
    #                    toolbar=False, submenu=False):
    #    """ Custom redefinition of fields_view_get to adapt the context
    #        to product variants.
    #    """
    #    res = super().fields_view_get(view_id=view_id,
    #                                  view_type=view_type,
    #                                  toolbar=toolbar,
    #                                  submenu=submenu)
    #    if view_type == 'form':
    #        update = False
    #        product_xml = etree.XML(res['arch'])
    #        manufacturer_path = "//field[@name='manufacturer_ids']"
    #        manufacturer_fields = product_xml.xpath(manufacturer_path)
    #        if manufacturer_fields:
    #            update = True
    #            manufacturer_field = manufacturer_fields[0]
    #            manufacturer_field.attrib['readonly'] = "0"
    #            manufacturer_field.attrib['context'] = \
    #                "{'search_default_product_id': active_id, 'default_product_tmpl_id': product_tmpl_id," \
    #                "'default_product_id': active_id}"
    #        properties_path = "//field[@name='product_prop_static_id']"
    #        properties_fields = product_xml.xpath(properties_path)
    #        _logger.info("VIEWS1 %s" % etree.tostring(properties_fields[0], pretty_print=True, encoding="unicode"))
    #        if properties_fields:
    #            update = True
    #            view = self.env.ref('product_properties.product_variant_easy_edit_manufacturer_view',
    #                                raise_if_not_found=False)
    #            properties_views = self.env['product.properties.static']._properties_print_view(view)
    #            _logger.info("VIEWS2 %s" % etree.tostring(properties_fields[0], pretty_print=True, encoding="unicode"))
    #        if update:
    #            res['arch'] = etree.tostring(product_xml)
    #            _logger.info("VIEWS3 %s" % etree.tostring(product_xml, pretty_print=True, encoding="unicode").replace(etree.tostring(properties_fields[0]), etree.tostring(properties_views)))
    #    return res

    @api.multi
    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False):
        self.ensure_one()
        if date is None:
            date = fields.Date.context_today(self)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        res = self.env['product.supplierinfo']
        sellers = self.seller_ids
        if self.env.context.get('force_company'):
            sellers = sellers.filtered(lambda s: not s.company_id or s.company_id.id == self.env.context['force_company'])
        if self._context.get('manufacturer_id', False):
            sellers = sellers.filtered(lambda r: r.manufacturer_id and r.manufacturer_id.id == self._context.get('manufacturer_id') or True)
        for seller in sellers:
            # Set quantity in UoM of seller
            quantity_uom_seller = quantity
            if quantity_uom_seller and uom_id and uom_id != seller.product_uom:
                quantity_uom_seller = uom_id._compute_quantity(quantity_uom_seller, seller.product_uom)
            divide_qty = seller.divide_qty > 0.0 or quantity_uom_seller

            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            if partner_id and seller.name not in [partner_id, partner_id.parent_id]:
                continue
            if float_compare(quantity_uom_seller, seller.min_qty, precision_digits=precision) == -1:
                continue
            if quantity_uom_seller % divide_qty != 0:
                continue
            if seller.product_id and seller.product_id != self:
                continue

            res |= seller
            break
        return res

    @api.onchange('product_prop_static_id')
    def _onchange_product_prop_static_id(self):
        for prod in self:
            if prod.product_prop_static_id:
                prod.categ_ids = False
                if prod.product_tmpl_id.product_variant_count == 1:
                    prod.categ_ids = (6, False, [x.id for x in self.env['product.properties.category'].search([('applicability', '=', 'template')])])
                else:
                    prod.categ_ids = (6, False, [x.id for x in self.env['product.properties.category'].search([('applicability', '=', 'product')])])
                prod._onchange_categ_ids()

    @api.onchange('categ_ids')
    def _onchange_categ_ids(self):
        for prod in self:
            if prod.product_tmpl_id.product_variant_count == 1:
                ret = []
                for categ in prod.categ_ids:
                    ret += prod._get_default_product_properties_ids(categ.lines_ids, categ_id=categ, product=prod.product_tmpl_id)
            else:
                ret = []
                for categ in prod.categ_ids:
                    ret += prod._get_default_product_properties_ids(categ.lines_ids, categ_id=categ, product=prod)

    @api.onchange('tcateg_ids')
    def _onchange_tcateg_ids(self):
        for prod in self:
            ret = []
            for categ in prod.tcateg_ids:
                ret += prod.product_tmpl_id._get_default_product_properties_ids(categ.lines_ids, categ_id=categ, product=prod.product_tmpl_id)

    def _get_default_product_properties_ids(self, properties, categ_id=False, product=False, default={}):
        system = False
        if not product:
            product = self
        if not properties:
            system = True
            properties = self.env['product.properties.type'].search([])
        res = []
        sequence = 0
        name_ids = [x.name.id for x in self.product_properties_ids]
        for rec in properties.sorted(key=lambda r: r.sequence):
            if default and default.get(rec.name.name):
                if rec.type_fields == 'int':
                    if default[rec.name.name]['value'] and default[rec.name.name]['value'].find(".") == -1:
                        type_int = int(default[rec.name.name]['value'])
                    elif default[rec.name.name]['value']:
                        type_float = float(default[rec.name.name]['value'])
                        type_fields = 'float'
                    else:
                        type_int = default[rec.name.name]['value']
                elif rec.type_fields == 'float':
                    type_float = float(default[rec.name.name]['value'])
                elif rec.type_fields == 'char':
                    type_char = default[rec.name.name]['value']
                elif rec.type_fields == 'range':
                    type_int = default[rec.name.name]['min']
                    type_int_second = default[rec.name.name]['max']
                elif rec.type_fields == 'package':
                    package = self.env['product.properties.package'].search([('name', '=', default[rec.name.name]['value'])])
                    if package:
                        type_package_id = package.id
                        type_char = rec.type_char
                    else:
                        type_package_id = rec.type_package_id.id
                        type_char = rec.type_char
                uom = self.env['product.properties.uom'].search([('name', '=', default[rec.name.name]['unit'])])
                if uom:
                    type_uom_id = uom.id
                else:
                    type_uom_id = rec.type_uom_id.id
            sequence += 1
            if rec.name.id not in name_ids:
                #_logger.info("LINE %s" % categ_id.id)
                #'product_id': product.product_variant_id.id,
                value = {'product_id': product.id,
                          'product_tmpl_id': 'product_tmpl_id' in product._fields and product.product_tmpl_id.id or False,
                          'sequence': sequence,
                          'name': system and rec.id or rec.name.id,
                          'categ_id': categ_id.id,
                          'type_fields': rec.type_fields,
                          'type_char': rec.type_char,
                          'type_int': rec.type_int,
                          'type_int_second': rec.type_int_second,
                          'type_float': rec.type_float,
                          'type_boolean': rec.type_boolean,
                          'type_package_id': rec.type_package_id and rec.type_package_id.id or False,
                          'type_field_model_id': rec.type_field_model_id and rec.type_field_model_id.id or False,
                          'type_field_target': rec.type_field_target and rec.type_field_target.id or False,
                          'dimensions_x': rec.dimensions_x,
                          'dimensions_y': rec.dimensions_y,
                          'dimensions_z': rec.dimensions_z,
                          'type_uom_id': rec.type_uom_id and rec.type_uom_id.id or False,
                          }
                line = self.env["product.properties"].new(value)
                res.append((0, False, line._convert_to_write(line._cache)))
        return res

    @api.multi
    def action_get_properties(self):
        for product in self:
            default = {}
            if product.product_properties_has:
                ret = product._get_default_product_properties_ids(default=default)
                product.product_properties_ids = ret

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        if len(res.product_properties_ids.ids) == 0:
            applicability = self.env['product.properties.category'].search([('applicability', '=', 'product')])
            #_logger.info("PRODUCT PROPERTIES %s:%s" % (applicability, res))
            if applicability:
                res.categ_ids = [(6, False, [x.id for x in applicability])]
            if len(res.product_tmpl_id.attribute_line_ids.ids) > 0:
                applicability = self.env['product.properties.category'].search([('applicability', '=', 'template')])
            else:
                applicability = self.env['product.properties.category'].search([('applicability', '=', 'templateoo')])
            if applicability:
                res.product_tmpl_id.categ_ids = [(6, False, [x.id for x in applicability])]
        return res

    @api.multi
    def write(self, vals):
        manufacturer = {}
        if vals.get('manufacturer_pname'):
            manufacturer.update(manufacturer_pname=vals['manufacturer_pname'])
        if vals.get('manufacturer_pref'):
            manufacturer.update(manufacturer_pref=vals['manufacturer_pref'])
        if vals.get('manufacturer_purl'):
            manufacturer.update(manufacturer_purl=vals['manufacturer_purl'])
        if manufacturer and not self.manufacturer:
            manufacturer.update(manufacturer=vals.get('manufacturer') and vals['manufacturer'] or self.product_tmpl_id.manufacturer_id.id)
            manufacturer.update(product_tmpl_id=self.product_tmpl_id.id)
            manufacturer.update(product_id=self.id)
            res = self.env['product.manufacturer'].create(manufacturer)
            vals['manufacturer'] = res.id
        return super(ProductProduct, self).write(vals)

    def _compute_datasheet_ids(self):
        for product in self:
            domain = ['|','|',
                      '&', ('res_model', '=', 'product.product'), ('res_id', '=', product.id),
                      '&', ('res_model', '=', 'res.partner'), ('res_id', '=', self.manufacturer_id.id),
                      '&', ('res_model', '=', 'product.brand'), ('res_id', '=', product.product_brand_id.id)
                      ]
            product.datasheet_ids = [x['id'] for x in self.env['product.manufacturer.datasheets'].search_read(domain, ['name'])]

    @api.one
    def _compute_has_datasheets(self):
        domain = ['|','|',
                    '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.id),
                    '&', ('res_model', '=', 'res.partner'), ('res_id', '=', self.manufacturer_id.id),
                    '&', ('res_model', '=', 'product.brand'), ('res_id', '=', self.product_brand_id.id)
                  ]
        nbr_datasheet = self.env['product.manufacturer.datasheets'].search_count(domain)
        self.count_datasheets = nbr_datasheet

    @api.multi
    def action_see_datasheets(self):
        domain = ['|','|',
                    '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.id),
                    '&', ('res_model', '=', 'res.partner'), ('res_id', '=', self.manufacturer_id.id),
                    '&', ('res_model', '=', 'product.brand'), ('res_id', '=', self.product_brand_id.id)
                  ]

        attachment_view = self.env.ref('product_properties.view_product_manufacturer_datasheets_eazy_kanban')
        return {
            'name': _('Datasheets'),
            'domain': domain,
            'res_model': 'product.manufacturer.datasheets',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                        Click to upload datasheet to your product.
                    </p><p>
                        Use this feature to store any files, like drawings or specifications.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d, 'default_manufacturer': %d, 'partner_id': %d}" % ('product.product', self.id, self.manufacturer.id, self.manufacturer_id)
            }


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    manufacturer_id = fields.Many2one("product.manufacturer", "Manufacturer info")
    manufacturer_pref = fields.Char(related="manufacturer_id.manufacturer_pref", string='Manuf. Product Code')
    manufacturer_pname = fields.Char(related="manufacturer_id.manufacturer_pname", string='Manuf. Product Name')
    divide_qty = fields.Float('Divide Quantity', default=1.0, required=True,
        help="The minimal quantity to purchase from this vendor, expressed in the vendor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")

    @api.onchange('manufacturer_id')
    def _onchange_manufacturer_id(self):
        if self.manufacturer_id and not self._context.get('default_manufacturer_id', False):
            manufacturer = self.env['product.manufacturer'].search([('id', '=', self.manufacturer_id.id)])
            if not manufacturer:
                manufacturer.write({
                    'supplierinfo_ids': (6, False, [manufacturer.supplierinfo_ids.ids] + [self.id])
                    })
