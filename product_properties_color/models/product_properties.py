# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)

class ProductPropertiesStaticDropdown(models.Model):
    _inherit = "product.properties.static.dropdown"

    color = fields.Integer(string="Color Index", compute='_compute_color_index', store=True)
    color_picker = fields.Selection([('0', 'Grey'),
                                     ('1', 'Green'),
                                     ('2', 'Yellow'),
                                     ('3', 'Orange'),
                                     ('4', 'Red'),
                                     ('5', 'Purple'),
                                     ('6', 'Blue'),
                                     ('7', 'Cyan'),
                                     ('8', 'Aquamarine'),
                                     ('9', 'Pink'),
                                     ('10', 'Light Green'),], string='Choice Color',
                                     required=True, default='0')

    @api.depends('color_picker')
    def _compute_color_index(self):
        for tag in self:
            tag.color = int(tag.color_picker)

    @api.onchange('color_picker')
    def onchange_color_picker(self):
        if self.color_picker:
            self.color = int(self.color_picker)
        return {}


class ProductPropertiesPrintCategory(models.Model):
    _name = "product.properties.print.category"
    _description = "Category Product properties for default printing"

    name = fields.Char('Property name', required=True, translate=True)
    type_ids = fields.One2many("product.properties.print.line.category", inverse_name="print_id", string="Property name")
    type_static_id = fields.Many2one("product.properties.static", 'Static Product properties')


class ProductPropertiesLineCategory(models.Model):
    _name = "product.properties.print.line.category"
    _description = "Category lines Product properties for default printing"

    def _get_field_name_filter(self):
        static_properties_obj = self.env['product.properties.static']
        ret = []
        for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields):
            field = static_properties_obj.fields_get(g)[g]
            ret.append((g, field['string']))
        return ret

    print_id = fields.Many2one('Property name', required=True,  index=True)
    sequence = fields.Integer("Sequence", default=1, index=True, help="The first in the sequence is the default one.")
    type_id = fields.Many2one("product.properties.type", string="Property name")
    static_field = fields.Selection(selection="_get_field_name_filter", string="Static Properties Field name")
    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('type_id', 'print_id')
    def _compute_display_name(self):
        for type in self:
            if type.type_id:
                type.display_name = "[%s] %s" % (type.type_id.sequence, type.type_id.name)
            else:
                type.display_name = "%s" % type.static_field