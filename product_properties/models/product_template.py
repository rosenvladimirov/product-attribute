# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
import base64
import json

from lxml import etree
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, except_orm, UserError

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_properties_has = fields.Boolean(compute="_compute_product_properties", string="Category Has Product properties")
    product_properties_ids = fields.One2many("product.properties", "product_tmpl_id", string='Product properties', domain=[('product_id', '=', False)])
    has_product_properties = fields.Boolean(compute="_compute_has_product_properties", string="Product has properties")

    categ_ids = fields.Many2many('product.properties.category', relation="product_tmpl_prop", string='Global Category properties')
    curr_categ_ids = fields.Many2many('product.properties.category', string='Category properties', compute='_compute_curr_categ_ids')

    manufacturer = fields.Many2one('product.manufacturer', string="Product Manufacturer", compute="_compute_manufacturer", store=True)
    manufacturer_pname = fields.Char(string='Manuf. Product Name', related="manufacturer.manufacturer_pname")
    manufacturer_pref = fields.Char(string='Manuf. Product Code', related='manufacturer.manufacturer_pref')
    manufacturer_purl = fields.Char(string='Manuf. Product URL', related='manufacturer.manufacturer_purl')
    manufacturer_id = fields.Many2one('res.partner', string='Manufacturer', related="manufacturer.manufacturer", store=True)

    manufacturer_ids = fields.One2many('product.manufacturer', 'product_tmpl_id', 'Manufacturers', domain=[('product_id', '=', False)])
    count_datasheets = fields.Integer('Count Datasheets', compute='_compute_has_datasheets')
    datasheet_ids = fields.One2many('product.manufacturer.datasheets', compute="_compute_datasheet_ids")

    massedit = fields.Boolean()

    def _compute_datasheet_ids(self):
        for product in self:
            if self.product_variant_count > 0:
                domain = ['|',
                          '&', ('res_model', '=', 'product.product'), ('res_id', 'in', product.product_variant_ids.ids),
                          '&', ('res_model', '=', 'product.brand'), ('res_id', '=', product.product_brand_id.id)
                          ]
            else:
                domain = ['|',
                          '&', ('res_model', '=', 'product.product'), ('res_id', '=', product.product_variant_id.id),
                          '&', ('res_model', '=', 'product.brand'), ('res_id', '=', product.product_brand_id.id)
                          ]
            product.datasheet_ids = [x['id'] for x in self.env['product.manufacturer.datasheets'].search_read(domain, ['name'])]

    @api.depends('manufacturer_ids')
    def _compute_manufacturer(self):
        for p in self:
            if len(p.manufacturer_ids.ids) > 0:
                p.manufacturer = p.manufacturer_ids[0]
                #if p.product_variant_count == 1:
                #    p.product_variant_id.manufacturer_id = p.manufacturer_ids[0]
            else:
                p.manufacturer = False

    @api.one
    @api.depends('product_properties_ids')
    def _compute_has_product_properties(self):
        if self.product_properties_ids:
            self.has_product_properties = len(self.product_properties_ids.ids) > 0
        else:
            self.has_product_properties = False

    @api.multi
    def _compute_product_properties(self):
        for record in self:
            if record.categ_id and record.categ_id.product_properties_ids:
                record.product_properties_has = True
            else:
                record.product_properties_has = False

    @api.one
    def _compute_curr_categ_ids(self):
        ids = list(set(self.product_properties_ids.mapped('categ_id').mapped('id')))
        #_logger.info("USASGET %s" % ids)
        if ids:
            self.curr_categ_ids = [(4, id, False) for id in ids]
        else:
            self.curr_categ_ids = False

    @api.onchange('categ_ids')
    def _onchange_categ_ids(self):
        for prod in self:
            ret = []
            for categ in prod.categ_ids:
                ret += prod._get_default_product_properties_ids(categ.lines_ids, categ_id=categ, product=prod)

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
                #'product_id': product.product_variant_id.id,
                value = {
                          'product_tmpl_id': product.id,
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

    @api.one
    def _compute_get_domain(self):
        if self.product_variant_count > 0:
            domain = ['|',
                        '&', ('res_model', '=', 'product.product'), ('res_id', 'in', self.product_variant_ids.ids),
                        '&', ('res_model', '=', 'product.brand'), ('res_id', '=', self.product_brand_id.id)
                      ]
        else:
            domain = ['|',
                        '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_variant_id.id),
                        '&', ('res_model', '=', 'product.brand'), ('res_id', '=', self.product_brand_id.id)
                      ]
        return domain

    @api.one
    def _compute_has_datasheets(self):
        if self.product_variant_count > 0:
            domain = ['|',
                        '&', ('res_model', '=', 'product.product'), ('res_id', 'in', self.product_variant_ids.ids),
                        '&', ('res_model', '=', 'product.brand'), ('res_id', '=', self.product_brand_id.id)
                      ]
        else:
            domain = ['|',
                        '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_variant_id.id),
                        '&', ('res_model', '=', 'product.brand'), ('res_id', '=', self.product_brand_id.id)
                      ]
        nbr_datasheet = self.env['product.manufacturer.datasheets'].search_count(domain)
        self.count_datasheets = nbr_datasheet

    @api.multi
    def action_see_datasheets(self):
        if self.product_variant_count > 0:
            domain = ['|',
                        '&', ('res_model', '=', 'product.product'), ('res_id', 'in', self.product_variant_ids.ids),
                        '&', ('res_model', '=', 'product.brand'), ('res_id', '=', self.product_brand_id.id)
                      ]
        else:
            domain = ['|',
                        '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_variant_id.id),
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
            'context': "{'default_res_model': '%s','default_res_id': %d, 'default_manufacturer': %d}" % ('product.product', self.product_variant_id.id, self.manufacturer.id)
            }

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Custom redefinition of fields_view_get to adapt the context
            to product template.
        """
        res = super().fields_view_get(view_id=view_id,
                                      view_type=view_type,
                                      toolbar=toolbar,
                                      submenu=submenu)
        if view_type == 'form':
            product_xml = etree.XML(res['arch'])
            product_path = "//field[@name='datasheet_ids']"
            product_fields = product_xml.xpath(product_path)
            if product_fields:
                product_field = product_fields[0]
                product_field.attrib['context'] = "{'default_res_model': '%s','default_res_id': %d, 'default_manufacturer': %d}" % ('product.product', self.product_variant_id.id, self.manufacturer.id)
                #product_field.attrib['domain'] = json.dumps(self._compute_get_domain())
                res['arch'] = etree.tostring(product_xml)
        return res

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        if vals.get('manufacturer_id'):
            #_logger.info('VALS %s' % vals)
            res.manufacturer_ids = [(0, False, {'manufacturer': res.manufacturer_id.id, 'product_tmpl_id': res.id})]
        return res

    @api.multi
    def write(self, vals):
        if vals.get('massedit') and vals.get('categ_ids'):
            category = self.env['product.properties.category'].search([('id', 'in', [x[1] for x in vals.get('categ_ids')])])
            _logger.info("LINE 1 %s:%s" % (vals.get('categ_ids'), category))
            #del vals['massedit']
            for prod in self:
                ret = []
                for categ in category:
                    ret += prod._get_default_product_properties_ids(categ.lines_ids, categ_id=categ, product=prod)
                    #_logger.info("LINE %s" % ret)
                if ret:
                    vals['product_properties_ids'] = ret
        for prod in self:
            if vals.get('manufacturer_id') and vals.get('manufacturer_id') not in [x.id for x in prod.manufacturer_ids.mapped('manufacturer')]:
                #_logger.info('VALS %s' % vals)
                prod.manufacturer_ids = [(0, False, {'manufacturer': prod.manufacturer_id.id, 'product_tmpl_id': prod.id})]
        return super(ProductTemplate, self).write(vals)
