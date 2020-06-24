# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, RedirectWarning, UserError, except_orm

import logging
_logger = logging.getLogger(__name__)


class ProductPricelistPrint(models.TransientModel):
    _inherit = "product.pricelist.print"

    print_properties = fields.One2many('product.pricelist.properties.print', 'pricelist_print_id', 'Print properties')
    use_product_properties = fields.Selection([
        ('description', _('Use descriptions')),
        ('properties', _('Use properties')),],
        string="Type product description",
        help="Choice type of the view for product description",
        default="description")

    @api.onchange('use_product_properties')
    def onchange_use_product_properties(self):
        if self.use_product_properties == 'properties':
            print_ids = False
            static_properties_obj = self.env['product.properties.static']
            print_properties = []
            print_static_ids = filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields)
            for r in self.product_ids:
                if print_ids:
                    print_ids |= r.product_properties_ids.mapped("name") | r.tproduct_properties_ids.mapped("name")
                else:
                    print_ids = r.product_properties_ids.mapped("name") | r.tproduct_properties_ids.mapped("name")
            for r in self.product_tmpl_ids:
                if print_ids:
                    print_ids |= r.product_properties_ids.mapped("name")
                else:
                    print_ids = r.product_properties_ids.mapped("name")
            for r in self.product_set_ids:
                if print_ids:
                    print_ids |= r.product_properties_ids.mapped("name")
                else:
                    print_ids = r.product_properties_ids.mapped("name")
            #_logger.info("UNION %s" % list(set(print_ids)))
            if (print_ids or print_static_ids) and not self.print_properties:
                if print_ids:
                    print_properties += [(0, False, {'name': x.id, 'pricelist_print_id': self.id, 'print': True, 'sequence': x.sequence}) for x in print_ids]
                if print_static_ids:
                    print_properties += [(0, False, {'static_field': x, 'pricelist_print_id': self.id, 'print': True, 'sequence': 9999}) for x in print_static_ids]
                self.print_properties = print_properties
        else:
            self.print_properties = False


class ProductPropertiesPrint(models.TransientModel):
    _name = "product.pricelist.properties.print"
    _description = "Pricelist Product properties for printing"
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
    pricelist_print_id = fields.Many2one("product.pricelist.print", string="Pricelist direct print")
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
