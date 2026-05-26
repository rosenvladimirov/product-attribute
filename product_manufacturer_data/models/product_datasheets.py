# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging

_logger = logging.getLogger(__name__)


class ProductManufacturerDatasheets(models.Model):
    _name = 'product.manufacturer.datasheets'
    _description = "Datasheets Document"
    _inherits = {
        'ir.attachment': 'ir_attachment_id',
    }
    _order = "version desc, id desc"

    ir_attachment_id = fields.Many2one('ir.attachment',
                                       string='Related attachment', required=True, ondelete='cascade')
    version = fields.Char('Version')
    active = fields.Boolean('Active', default=True)
    manufacturer_id = fields.Many2one('product.manufacturer',
                                      string='Product Manufacturer')
    manufacturer_ids = fields.Many2many('product.manufacturer',
                                        string='Products Manufacturer')
    product_brand_id = fields.Many2one('product.brand',
                                       string='Brand',
                                       help='Select a brand for this product')
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    iso_number = fields.Char('Certificate Number')
    date_issue = fields.Date('Issue Date')
    date_expiry = fields.Date('Expiry Date')
    notified_body_id = fields.Many2one('res.partner', 'Notified Body')
    qc_manager_id = fields.Many2one(
        'res.users',
        'QC Manager',
        help='The internal user that is responsible for Quality Control.'
    )
    is_date = fields.Boolean('Has Expiry Date')

