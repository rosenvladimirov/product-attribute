# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, Command

from odoo.tools import float_compare

import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    manufacturer = fields.Many2one('product.manufacturer', string="Product Manufacturer")
    manufacturer_pname = fields.Char(string='Manuf. Product Name', related="manufacturer.manufacturer_pname")
    manufacturer_pref = fields.Char(string='Manuf. Product Code', related='manufacturer.manufacturer_pref')
    manufacturer_purl = fields.Char(string='Manuf. Product URL', related='manufacturer.manufacturer_purl')

    @api.onchange('manufacturer_pname', 'manufacturer_pref', 'manufacturer_purl')
    def _onchange_manufacturer_data(self):
        if not self.manufacturer and self.product_tmpl_id.product_variant_count > 1:
            self.update({'manufacturer': [0, False, {'manufacturer': self.product_tmpl_id.manufacturer_id.id,
                                                     'product_tmpl_id': self.product_tmpl_id.id,
                                                     'product_id': self.id,
                                                     'manufacturer_pname': self.manufacturer_pname,
                                                     'manufacturer_pref': self.manufacturer_pref,
                                                     'manufacturer_purl': self.manufacturer_purl}]})


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    manufacturer_id = fields.Many2one("product.manufacturer", "Manufacturer info")
    manufacturer_pref = fields.Char(related="manufacturer_id.manufacturer_pref", string='Manuf. Product Code')
    manufacturer_pname = fields.Char(related="manufacturer_id.manufacturer_pname", string='Manuf. Product Name')
    divide_qty = fields.Float('Divide Quantity', default=1.0, required=True,
                              help="The minimal quantity to purchase from this vendor, "
                                   "expressed in the vendor Product Unit of Measure if not any, "
                                   "in the default unit of measure of the product otherwise.")

    @api.onchange('manufacturer_id')
    def _onchange_manufacturer_id(self):
        if self.manufacturer_id and not self._context.get('default_manufacturer_id', False):
            manufacturer = self.env['product.manufacturer'].search([('id', '=', self.manufacturer_id.id)])
            if not manufacturer:
                manufacturer.write({
                    'supplierinfo_ids': (6, False, [manufacturer.supplierinfo_ids.ids] + [self.id])
                })
