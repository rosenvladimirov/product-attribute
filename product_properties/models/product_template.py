# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
import base64

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, except_orm, UserError

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_default_product_properties_ids(self, product=False, default={}):
        if not product:
            product = self.product_variant_id
        ret = []
        for rec in self.categ_id.product_properties_ids:
            type_fields = rec.type_fields
            type_int = rec.type_int
            type_int_second = rec.type_int_second
            type_char = rec.type_char
            type_float = rec.type_float
            type_package_id = rec.type_package_id.id
            type_uom_id = rec.type_uom_id.id

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

            res = self.env["product.properties"].new({
                                                      'product_id': product.id,
                                                      'sequence': rec.sequence,
                                                      'name': rec.name.id,
                                                      'type_fields': type_fields,
                                                      'type_char': type_char,
                                                      'type_int': type_int,
                                                      'type_int_second': type_int_second,
                                                      'type_float': type_float,
                                                      'type_boolean': rec.type_boolean,
                                                      'type_package_id': type_package_id,
                                                      'dimensions_x': rec.dimensions_x,
                                                      'dimensions_y': rec.dimensions_y,
                                                      'dimensions_z': rec.dimensions_z,
                                                      'type_uom_id': type_uom_id,
                                                      'image': rec.image,
                                                            })
            ret.append((0, False, res._convert_to_write(res._cache)))
        return ret

    product_properties_has = fields.Boolean(compute="_compute_product_properties", string="Categorie Product properties")
    product_properties_ids = fields.Many2many("product.properties", string='Product properties', domain="[('product_id', '=', product_variant_id.id)]", default=_get_default_product_properties_ids)
    has_product_properties= fields.Boolean(compute="_compute_has_product_properties", string="Categorie Product properties")

    manufacturer = fields.Many2one('product.manufacturer', string="Product Manufacturer", compute="_compute_manufacturer", store=True)
    manufacturer_pname = fields.Char(string='Manuf. Product Name', related="manufacturer.manufacturer_pname")
    manufacturer_pref = fields.Char(string='Manuf. Product Code', related='manufacturer.manufacturer_pref')
    manufacturer_purl = fields.Char(string='Manuf. Product URL', related='manufacturer.manufacturer_purl')
    manufacturer_id = fields.Many2one(comodel_name='res.partner', string='Manufacturer', related="manufacturer.manufacturer", store=True)

    manufacturer_ids = fields.One2many('product.manufacturer', 'product_tmpl_id', 'Manufacturers')
    variant_manufacturer_ids = fields.One2many('product.manufacturer', 'product_tmpl_id')
    count_datasheets = fields.Integer('Count Datasheets', compute='_compute_has_datasheets')

    @api.depends('manufacturer_ids')
    def _compute_manufacturer(self):
        for p in self:
            if len(p.variant_manufacturer_ids.ids) > 0:
                p.manufacturer = p.variant_manufacturer_ids[0]
            else:
                p.manufacturer = False

    @api.one
    @api.depends('product_properties_ids')
    def _compute_has_product_properties(self):
        self.has_product_properties = len(self.product_properties_ids.ids) > 0

    @api.multi
    def _compute_product_properties(self):
        for record in self:
            if record.categ_id and record.categ_id.product_properties_ids:
                record.product_properties_has = True
            else:
                record.product_properties_has = False

    @api.multi
    def action_get_properties(self):
        for product in self:
            default = {}
            if product.product_properties_has:
                ret = product._get_default_product_properties_ids(default=default)
                product.product_properties_ids = ret

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

        attachment_view = self.env.ref('product_properties.view_datasheets_file_kanban_properties')
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
            'context': "{'default_res_model': '%s','default_res_id': %d}" % ('product.product', self.product_variant_id.id)
            }
