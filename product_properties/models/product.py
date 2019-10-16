# -*- coding: utf-8 -*-

import requests
import base64
from lxml import etree

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


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
    manufacturer = fields.Many2one(comodel_name='res.partner', string='Manufacturer',)
    manufacturer_pname = fields.Char(string='Manuf. Product Name', translate=True)
    manufacturer_pref = fields.Char(string='Manuf. Product Code')
    manufacturer_purl = fields.Char(string='Manuf. Product URL')
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
        "Big-sized image", compute='_compute_images', inverse='_set_image',
        help="Image of the product variant (Big-sized image of product template if false). It is automatically "
             "resized as a 1024x1024px image, with aspect ratio preserved.")
    image_small = fields.Binary(
        "Small-sized image", compute='_compute_images', inverse='_set_image_small',
        help="Image of the product variant (Small-sized image of product template if false).")
    image_medium = fields.Binary(
        "Medium-sized image", compute='_compute_images', inverse='_set_image_medium',
        help="Image of the product variant (Medium-sized image of product template if false).")

    supplierinfo_ids = fields.Many2many("product.supplierinfo",
                                        relation="rel_mnf_suppinfo",
                                        column1="manufacturer_id",
                                        column2="supplierinfo_id",
                                        string='Product destributor')
    product_variant_count = fields.Integer('Variant Count', related='product_tmpl_id.product_variant_count')
    product_variant_ids = fields.One2many(related='product_tmpl_id.product_variant_ids', string='Products')
    packaging_ids = fields.One2many(
        'product.packaging', string="Product Packages", compute="_compute_packaging_ids", inverse="_set_packaging_ids",
        help="Gives the different ways to package the same product.")
    type = fields.Selection(related="product_tmpl_id.type")
    has_datasheets = fields.Boolean('Has Datasheets', compute='_compute_has_datasheets')
    count_datasheets = fields.Integer('Count Datasheets', compute='_compute_has_datasheets')

    #datasheet = fields.Binary(string="Datasheet", track_visibility="onchange")
    #fname = fields.Char(string="File Name", track_visibility="onchange")

    @api.depends('manufacturer', 'product_tmpl_id')
    def name_get(self):
        result = []
        for manufacturer in self:
            if self._context.get('display_code', False):
                name = "%s%s" % (manufacturer.product_tmpl_id and "[%s] " % manufacturer.product_tmpl_id.name or "", manufacturer.manufacturer.name)
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
                    product = vals.get('product_tmpl_id') and self.env['product.template'].browse(vals.get('product_tmpl_id')) or self.product_tmpl_id
                if vals.get('product_id', False) or self.product_id:
                    product = vals.get('product_id') and self.env['product.product'].browse(vals.get('product_id')) or self.product_id
                product.write({'packaging_ids': (6, False, [product.packaging_ids] + vals['packaging_ids'][2])})
        return super(ProductManufacturer, self).write(vals)

    @api.one
    @api.depends('product_id')
    def _compute_has_datasheets(self):
        if self.product_variant_count > 0 and self.product_id:
            domain = ['|',
                '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_id.id),
                '&', ('res_model', '=', 'product.brand'), ('id', '=', self.product_id.product_tmpl_id.product_brand_id.id),
                "|", ('manufacturer_id', '=', False), ('manufacturer_id', '=', self.id)]
        else:
            domain = ['|',
                '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_variant_id.id),
                '&', ('res_model', '=', 'product.brand'), ('id', '=', self.product_tmpl_id.product_brand_id.id),
                "|", ('manufacturer_id', '=', False), ('manufacturer_id', '=', self.id)]
        nbr_datasheet = self.env['product.manufacturer.datasheets'].search_count(domain)
        self.has_datasheets = bool(nbr_datasheet)
        self.count_datasheets = nbr_datasheet

    @api.multi
    def action_see_datasheets(self):
        if self.product_variant_count > 0 and self.product_id:
            domain = ['|',
                '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_id.id),
                '&', ('res_model', '=', 'product.brand'), ('id', '=', self.product_id.product_tmpl_id.product_brand_id.id),
                "|", ('manufacturer_id', '=', False), ('manufacturer_id', '=', self.id)]
        else:
            domain = ['|',
                '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_variant_id.id),
                '&', ('res_model', '=', 'product.brand'), ('id', '=', self.product_tmpl_id.product_brand_id.id),
                "|", ('manufacturer_id', '=', False), ('manufacturer_id', '=', self.id)]

        attchment_view = self.env.ref('product_properties.view_datasheets_file_kanban_properties')
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
            'context': "{'default_res_model': '%s','default_res_id': %d, 'default_manufacturer_id': %d}" % ('product.product', (self.product_variant_count > 1 and self.product_id) and self.product_id.id or self.product_variant_id.id, self.id)
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
    product_brand_id = fields.Many2one('product.brand', string='Brand', help='Select a brand for this product')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_default_product_properties_ids(self, product=False, default={}):
        if not product:
            product = self
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
    product_properties_ids = fields.Many2many("product.properties", string='Product properties', domain="[('product_id', '=', id)]", default=_get_default_product_properties_ids)
    has_product_properties= fields.Boolean(compute="_compute_has_product_properties", string="Categorie Product properties")

    manufacturer = fields.Many2one('product.manufacturer', string="Product Manufacturer", compute="_compute_manufacturer", store=True)
    manufacturer_pname = fields.Char(string='Manuf. Product Name', related="manufacturer.manufacturer_pname")
    manufacturer_pref = fields.Char(string='Manuf. Product Code', related='manufacturer.manufacturer_pref')
    manufacturer_purl = fields.Char(string='Manuf. Product URL', related='manufacturer.manufacturer_purl')
    manufacturer_ids = fields.Many2many("product.manufacturer",
                                        relation="rel_product_mnf",
                                        column1="product_id",
                                        column2="manufacturer_id",
                                        string='Product manufacturer')
    manufacturer_id = fields.Many2one(comodel_name='res.partner', string='Manufacturer', related="manufacturer.manufacturer", store=True)

    @api.multi
    def _compute_product_properties(self):
        for record in self:
            if record.product_tmpl_id.categ_id and record.product_tmpl_id.categ_id.product_properties_ids:
                record.product_properties_has = True
            else:
                record.product_properties_has = False

    @api.one
    @api.depends('product_properties_ids')
    def _compute_has_product_properties(self):
        self.has_product_properties = len(self.product_properties_ids.ids) > 0


    @api.depends('manufacturer_ids', 'product_tmpl_id.manufacturer')
    def _compute_manufacturer(self):
        for p in self:
            if p.product_tmpl_id.manufacturer:
                p.manufacturer = p.product_tmpl_id.manufacturer
            else:
                p.manufacturer = p.manufacturer_ids[0]

    @api.one
    def _get_manufacturer_ids(self):
        ids = self.env['product.manufacturer'].search([
            '|',
            ('product_id', '=', self.id),
            ('product_tmpl_id', '=', self.product_tmpl_id.id)]).ids
        if ids:
            self.manufacturer_ids = (6, False, ids)
        else:
            self.manufacturer_ids = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """ Custom redefinition of fields_view_get to adapt the context
            to product variants.
        """
        res = super().fields_view_get(view_id=view_id,
                                      view_type=view_type,
                                      toolbar=toolbar,
                                      submenu=submenu)
        if view_type == 'form':
            product_xml = etree.XML(res['arch'])
            manufacturer_path = "//field[@name='manufacturer_ids']"
            manufacturer_fields = product_xml.xpath(manufacturer_path)
            if manufacturer_fields:
                manufacturer_field = manufacturer_fields[0]
                manufacturer_field.attrib['readonly'] = "0"
                manufacturer_field.attrib['context'] = \
                    "{'search_default_product_id': active_id, 'default_product_tmpl_id': product_tmpl_id," \
                    "'default_product_id': active_id}"
                res['arch'] = etree.tostring(product_xml)
        return res

    @api.multi
    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False):
        res = super(ProductProduct, self)._select_seller(partner_id=partner_id, quantity=quantity, date=date, uom_id=uom_id)
        if self.env.context.get('manufacturer_id', False):
            return res.filtered(lambda r: r.manufacturer_id == self.env.context.get('manufacturer_id'))
        return res

    @api.multi
    def action_get_properties(self):
        for product in self:
            default = {}
            if product.product_properties_has:
                ret = product._get_default_product_properties_ids(default=default)
                product.product_properties_ids = ret
                #product.write({'product_properties_ids': ret})


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    manufacturer_id = fields.Many2one("product.manufacturer", "Manufacturer info")
    manufacturer_pref = fields.Char(related="manufacturer_id.manufacturer_pref", string='Manuf. Product Code')
    manufacturer_pname = fields.Char(related="manufacturer_id.manufacturer_pname", string='Manuf. Product Name')

    @api.onchange('manufacturer_id')
    def _onchange_manufacturer_id(self):
        if self.manufacturer_id:
            manufacturer = self.env['product.manufacturer'].search([('id', '=', self.manufacturer_id.id)])
            _logger.info("Manufacturer %s:%s" % (manufacturer.supplierinfo_ids.ids, self.id))
            if not manufacturer:
                manufacturer.write({
                    'supplierinfo_ids': (6, False, [manufacturer.supplierinfo_ids.ids] + [self.id])
                    })
