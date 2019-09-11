# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
import base64
from lxml import etree
import os
import json

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

_img_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static/src/img'))


class ProductManufacturer(models.Model):
    _name = "product.manufacturer"
    _description = "Information about a product manufacturer"

    @api.depends('manufacturer', 'manufacturer_pref')
    def _compute_display_name(self):
        for mnf in self:
            if mnf.manufacturer_pref:
                mnf.display_name = "[%s] %s" % (mnf.manufacturer_pref, mnf.manufacturer.display_name)
            else:
                mnf.display_name = "%s" % mnf.manufacturer.display_name
            if 'reelpackaging_ids' in self._fields and mnf.reelpackaging_ids:
                mnf.name = "%s (%s %s)" % (mnf.manufacturer.display_name, mnf.reelpackaging_ids[0].name, _('Unit(s)'))
            else:
                mnf.name = "%s" % mnf.manufacturer.display_name

    active = fields.Boolean('Active', default=True,
                            help="If the active field is set to False, it will allow you to hide the bills of material without removing it.")
    sequence = fields.Integer(index=True, default=1)
    display_name = fields.Char("Manuf. Name", compute=_compute_display_name)
    manufacturer = fields.Many2one(comodel_name='res.partner', string='Manufacturer', )
    manufacturer_pname = fields.Char(string='Manuf. Product Name', translate=True)
    manufacturer_pref = fields.Char(string='Manuf. Product Code')
    manufacturer_purl = fields.Char(string='Manuf. Product URL')

    # link_compl_url = fields.Char(help="Compliance Policy")
    # link_qc_url = fields.Char(help="Quality Policy")
    # form_rma_url = fields.Char(help="RMA Form")
    # form_po_url = fields.Char(help="Order Form")
    # form_compl_url = fields.Char(help="Complaint Form")
    # form_incident_url = fields.Char(help="Incident Report Form")
    # form_loaner_url = fields.Char(help="Loaner Form")

    name = fields.Char("Manuf. Name", compute=_compute_display_name, store=True)
    product_brand_id = fields.Many2one('product.brand', string='Brand', help='Select a brand for this product')

    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get('product.template'), index=1)

    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template', ondelete='cascade',
        help="Specify a template if this rule only applies to one product template. Keep empty otherwise.")
    product_id = fields.Many2one(
        'product.product', 'Product variant', ondelete='cascade',
        help="Specify a product if this rule only applies to one product. Keep empty otherwise.")
    product_variant_id = fields.Many2one('product.product', 'Product', compute='_compute_product_variant_id')

    image = fields.Binary(
        "Big-sized image", related="product_id.image",
        help="Image of the product variant (Big-sized image of product template if false). It is automatically "
             "resized as a 1024x1024px image, with aspect ratio preserved.")
    image_small = fields.Binary(
        "Small-sized image", related="product_id.image_small",
        help="Image of the product variant (Small-sized image of product template if false).")
    image_medium = fields.Binary(
        "Medium-sized image", related="product_id.image_medium",
        help="Image of the product variant (Medium-sized image of product template if false).")

    supplierinfo_ids = fields.Many2many("product.supplierinfo",
                                        relation="rel_mnf_suppinfo",
                                        column1="manufacturer_id",
                                        column2="supplierinfo_id",
                                        string='Product destributor')
    #notified_body_ids = fields.Many2many('res.partner', string='Sertificates Notified Body', related='manufacturer.notified_body_ids')

    product_variant_count = fields.Integer('Variant Count', related='product_tmpl_id.product_variant_count')
    product_variant_ids = fields.One2many(related='product_tmpl_id.product_variant_ids', string='Products')
    packaging_ids = fields.One2many(
        'product.packaging', string="Product Packages", compute="_compute_packaging_ids", inverse="_set_packaging_ids",
        help="Gives the different ways to package the same product.")
    type = fields.Selection(related="product_tmpl_id.type")
    has_datasheets = fields.Boolean('Has Datasheets', compute='_compute_has_datasheets')
    count_datasheets = fields.Integer('Count Datasheets', compute='_compute_has_datasheets')
    product_brand_ids = fields.One2many('product.brand', 'manufacturer', string='Product brands')

    # datasheet_ids = fields.One2many('product.manufacturer.datasheets', 'product_tmpl_id')
    # datasheet = fields.Binary(string="Datasheet", track_visibility="onchange")
    # fname = fields.Char(string="File Name", track_visibility="onchange")

    @api.depends('manufacturer', 'product_tmpl_id')
    def name_get(self):
        result = []
        for manufacturer in self:
            if self._context.get('display_code', False):
                name = "%s%s" % (manufacturer.product_tmpl_id and "[%s] " % manufacturer.product_tmpl_id.name or "",
                                 manufacturer.manufacturer.name)
            else:
                name = manufacturer.manufacturer.name
            result.append((manufacturer.id, name))
        return result

    @api.depends('product_variant_ids', 'product_variant_ids.packaging_ids', 'product_id', 'product_id.packaging_ids')
    def _compute_packaging_ids(self):
        for p in self:
            if len(p.product_variant_ids) == 1:
                p.packaging_ids = p.product_variant_id.packaging_ids
            else:
                p.packaging_ids = p.product_variant_ids.mapped('packaging_ids')

    def _set_packaging_ids(self):
        for p in self:
            if len(p.product_variant_ids) == 1:
                p.product_variant_id.packaging_ids = p.packaging_ids
            else:
                p.product_variant_ids.packaging_ids = p.packaging_ids

    @api.depends('product_variant_ids')
    def _compute_product_variant_id(self):
        for p in self:
            p.product_variant_id = p.product_variant_ids[:1].id

    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        return super(ProductManufacturer, self).create(vals)

    @api.multi
    def write(self, vals):
        for product_template in self:
            default = {}
            if 'packaging_ids' in vals:
                if vals.get('product_tmpl_id', False) or self.product_tmpl_id:
                    product = vals.get('product_tmpl_id') and self.env['product.template'].browse(
                        vals.get('product_tmpl_id')) or self.product_tmpl_id
                if vals.get('product_id', False) or self.product_id:
                    product = vals.get('product_id') and self.env['product.product'].browse(
                        vals.get('product_id')) or self.product_id
                product.write({'packaging_ids': (6, False, [product.packaging_ids] + vals['packaging_ids'][2])})
        return super(ProductManufacturer, self).write(vals)

    @api.one
    @api.depends('product_id')
    def _compute_has_datasheets(self):
        if self.product_variant_count > 0 and self.product_id:
            domain = ['|',
                      '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_id.id),
                      '&', ('res_model', '=', 'product.brand'),
                      ('id', '=', self.product_id.product_tmpl_id.product_brand_id.id),
                      "|", ('manufacturer_id', '=', False), ('manufacturer_id', '=', self.id)]
        else:
            domain = ['|',
                      '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_variant_id.id),
                      '&', ('res_model', '=', 'product.brand'), ('id', '=', self.product_tmpl_id.product_brand_id.id),
                      "|", ('manufacturer', '=', False), ('manufacturer', '=', self.id)]
        nbr_datasheet = self.env['product.manufacturer.datasheets'].search_count(domain)
        self.has_datasheets = bool(nbr_datasheet)
        self.count_datasheets = nbr_datasheet

    @api.multi
    def action_see_datasheets(self):
        if self.product_variant_count > 0 and self.product_id:
            domain = ['|',
                      '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_id.id),
                      '&', ('res_model', '=', 'product.brand'),
                      ('id', '=', self.product_id.product_tmpl_id.product_brand_id.id),
                      "|", ('manufacturer', '=', False), ('manufacturer', '=', self.id)]
        else:
            domain = ['|',
                      '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_variant_id.id),
                      '&', ('res_model', '=', 'product.brand'), ('id', '=', self.product_tmpl_id.product_brand_id.id),
                      "|", ('manufacturer', '=', False), ('manufacturer', '=', self.id)]

        attchment_view = self.env.ref('product_properties.view_product_manufacturer_datasheets_eazy_kanban')
        return {
            'name': _('Datasheets'),
            'domain': domain,
            'res_model': 'product.manufacturer.datasheets',
            'type': 'ir.actions.act_window',
            'view_id': attchment_view.id,
            'views': [(attchment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                        Click to upload datasheet to your product.
                    </p><p>
                        Use this feature to store any files, like drawings or specifications.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d, 'default_manufacturer_id': %d}" % (
            'product.product',
            (self.product_variant_count > 1 and self.product_id) and self.product_id.id or self.product_variant_id.id,
            self.id)
        }


class ProductManufacturerDatasheets(models.Model):
    _name = 'product.manufacturer.datasheets'
    _description = "Datasheets Document"
    _inherits = {
        'ir.attachment': 'ir_attachment_id',
    }
    _order = "version desc, id desc"

    ir_attachment_id = fields.Many2one('ir.attachment', string='Related attachment', required=True, ondelete='cascade')
    active = fields.Boolean('Active', default=True)
    version = fields.Char('Version')
    manufacturer_id = fields.Many2one('product.manufacturer', 'Manufacturer')
    manufacturer = fields.Many2one('res.partner', string='Manufacturer', related="manufacturer_id.manufacturer", store=True)
    product_brand_id = fields.Many2one('product.brand', string='Brand', help='Select a brand for this product')
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    iso_number = fields.Char('Certificate Number')
    date_issue = fields.Date('Issue Date')
    date_expiry = fields.Date('Expiry Date')
    notified_body_id = fields.Many2one('res.partner', 'Notified Body')
    #notified_body_ids = fields.Many2many('res.partner', string='Sertificates Notified Body', related='manufacturer_id.notified_body_ids')

    qc_manager_id = fields.Many2one('res.users', 'QC Manager',
                                    help='The internal user that is resposnsible for Quality Control.')
    is_date = fields.Boolean('Has Expiry Date')
    color = fields.Integer(string="Color")
    custom_thumbnail = fields.Binary(string="Custom Thumbnail")
    custom_thumbnail_medium = fields.Binary(string="Medium Custom Thumbnail")
    custom_thumbnail_small = fields.Binary(string="Small Custom Thumbnail")
    thumbnail = fields.Binary(compute='_compute_thumbnail', string="Thumbnail")
    thumbnail_medium = fields.Binary(compute='_compute_thumbnail_medium', string="Medium Thumbnail")
    thumbnail_small = fields.Binary(compute='_compute_thumbnail_small', string="Small Thumbnail")

    @api.depends('custom_thumbnail')
    def _compute_thumbnail(self):
        for record in self:
            if record.custom_thumbnail:
                record.thumbnail = record.with_context({}).custom_thumbnail
            else:
                extension = record.mimetype.split("/")[1]
                if record.url:
                    extension = record.url.replace('http://', '').replace('https://', '').split("/")[0].split('.')[0]
                path = os.path.join(_img_path, "file_%s.png" % extension)
                if not os.path.isfile(path):
                    path = os.path.join(_img_path, "file_unkown.png")
                with open(path, "rb") as image_file:
                    record.thumbnail = base64.b64encode(image_file.read())

    @api.depends('custom_thumbnail_medium')
    def _compute_thumbnail_medium(self):
        for record in self:
            if record.custom_thumbnail_medium:
                record.thumbnail_medium = record.with_context({}).custom_thumbnail_medium
            else:
                extension = record.mimetype.split("/")[1]
                if record.url:
                    extension = record.url.replace('http://', '').replace('https://', '').split("/")[0].split('.')[0]
                path = os.path.join(_img_path, "file_%s_128x128.png" % extension)
                if not os.path.isfile(path):
                    path = os.path.join(_img_path, "file_unkown_128x128.png")
                with open(path, "rb") as image_file:
                    record.thumbnail_medium = base64.b64encode(image_file.read())

    @api.depends('custom_thumbnail_small')
    def _compute_thumbnail_small(self):
        for record in self:
            if record.custom_thumbnail_small:
                record.thumbnail_small = record.with_context({}).custom_thumbnail_small
            else:
                extension = record.mimetype.split("/")[1]
                if record.url:
                    extension = record.url.replace('http://', '').replace('https://', '').split("/")[0].split('.')[0]
                path = os.path.join(_img_path, "file_%s_64x64.png" % extension)
                if not os.path.isfile(path):
                    path = os.path.join(_img_path, "file_unkown_64x64.png")
                with open(path, "rb") as image_file:
                    record.thumbnail_small = base64.b64encode(image_file.read())
