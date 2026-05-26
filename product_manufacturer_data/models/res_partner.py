# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    product_manufacture_ids = fields.One2many('product.manufacturer',
                                              'manufacturer_id',
                                              string='Products')
    is_manufacturer = fields.Boolean('Manufacturer',
                                     compute='_compute_is_manufacturer',
                                     search='_search_is_manufacturer')
    distributor_ids = fields.Many2many('product.supplierinfo',
                                       compute='_compute_distributor_ids')
    has_distributor = fields.Boolean('It is distributor',
                                     compute='_compute_has_distributor')

    authorised_id = fields.Many2one('res.partner', 'Authorised Representative')
    qc_manager_id = fields.Many2one('res.partner', 'Quality Manager')
    req_manager_id = fields.Many2one('res.partner', 'Regulatory Manager')
    compliance_manager_id = fields.Many2one('res.partner', 'Compliance Manager')
    product_brand_ids = fields.One2many('product.brand', 'partner_id', string='Product brands')

    @api.model
    def _search_is_manufacturer(self, operator, value):
        # Handle the search logic based on the operator and value
        return [('product_manufacture_ids', '!=', False)] if value else [('product_manufacture_ids', '=', False)]

    @api.depends('product_manufacture_ids')
    def _compute_is_manufacturer(self):
        for record in self:
            record.is_manufacturer = len(record.product_manufacture_ids.ids) > 0

    @api.depends('distributor_ids')
    def _compute_has_distributor(self):
        for record in self:
            record.has_distributor = len(record.distributor_ids.ids) > 0

    def _compute_distributor_ids(self):
        for partner in self:
            if partner.product_manufacture_ids:
                distributor_ids = []
                for x in partner.product_manufacture_ids:
                    distributor_ids += [s.id for s in x.supplierinfo_ids]
                if distributor_ids:
                    partner.distributor_ids = [(6, False, distributor_ids)]
                else:
                    partner.distributor_ids = False
            else:
                partner.distributor_ids = False
