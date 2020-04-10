# -*- coding: utf-8 -*-
# dXFactory Proprietary License (dXF-PL) v1.0. See LICENSE file for full copyright and licensing details.

import itertools
import psycopg2
import re

from odoo.addons import decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, except_orm
from odoo.tools import pycompat


class ProductTemplate(models.Model):
    _inherit = "product.template"

    description_short = fields.Char("Short description", size=19, translate=True, required=True, index=True)
    label_prefix_id = fields.Many2one("product.template.label.prefix", string="Label Prefix")
    label_prefix_code = fields.Char(related="label_prefix_id.code", string="Label Prefix", store=True)
    label_separator = fields.Char(related="label_prefix_id.separator", string="Label Prefix", store=True)
    alternative_component_ids = fields.Many2many('product.template', 'product_alternative_component_rel', 'src_id', 'dest_id',
                                               string='Alternative Components', help='Suggest more expensive alternatives to '
                                               'components. Those products to be possible to replace is scheme.')


    @api.model
    def create(self, vals):
        if 'description_short' not in vals:
            vals['description_short'] = vals['name'][:19]
        res = super(ProductTemplate, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        for record in self:
            if 'default_code' in vals and 'barcode' not in vals and not record.barcode:
                default_code = re.sub('[^0-9]', '', vals['default_code'])
                if default_code and default_code != "":
                    vals['barcode'] = self.env['barcode.nomenclature'].sanitize_ean(default_code)
            res = super(ProductTemplate, self).write(vals)
            return res


class ProductTemplateLabelPrefix(models.Model):
    _name = "product.template.label.prefix"
    _descripton = "Product Label Prefix"

    @api.depends("name", "code")
    def _compute_display_name(self):
        for product in self:
            product.display_name = "[%s] %s" % (product.code, product.name)

    code = fields.Char("Code")
    name = fields.Char("Name")
    display_name = fields.Char("Display name", compute=_compute_display_name)
    separator = fields.Char("Separator")
