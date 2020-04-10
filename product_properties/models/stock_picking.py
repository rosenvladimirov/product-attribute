# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    print_properties = fields.One2many('product.properties.print', 'picking_id', 'Print properties')
    #use_product_description = fields.Boolean(default=True)
    use_product_properties = fields.Selection([
        ('description', _('Use descriptions')),
        ('properties', _('Use properties')),],
        string="Type product description",
        help='Choice type of the view for product description',
        default="description")
    product_prop_static_id = fields.Many2one("product.properties.static", 'Static Product properties')
    invoice_sub_type = fields.Many2one(related="product_prop_static_id.invoice_sub_type")

    @api.multi
    def remove_all_print_properties(self):
        for record in self:
            record.print_properties =  False

    @api.multi
    def set_all_print_properties(self):
        print_ids = False
        for record in self:
            static_properties_obj = self.env['product.properties.static']
            print_properties = []
            print_static_ids = filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields)
            partner_print_ids = [x.id for x in record.partner_id.print_properties if x.print]
            for r in record.move_lines.mapped('product_id'):
                print_ids = r.product_properties_ids | r.tproduct_properties_ids
                #if partner_print_ids:
                #    print_ids = print_ids.filtered(lambda r: r.id in partner_print_ids)
            if (print_ids or print_static_ids) and not record.print_properties:
                if print_ids:
                    print_properties += [(0, False, {'name': x.name.id, 'picking_id': self.id, 'print': True, 'sequence': x.sequence}) for x in print_ids if x.name]
                if print_static_ids:
                    print_properties += [(0, False, {'static_field': x, 'picking_id': self.id, 'print': True, 'sequence': 9999}) for x in print_static_ids]
                #_logger.info("LIST %s" % print_properties)
                record.print_properties = print_properties

    @api.model
    def create(self, vals):
        res = super(Picking, self).create(vals)
        vals = self.env['product.properties.static'].static_property_data(res, vals)
        return res

    @api.multi
    def write(self, vals):
        if 'product_prop_static_id' not in vals:
            for record in self:
                vals = self.env['product.properties.static'].static_property_data(record, vals)
        return super(Picking, self).write(vals)
