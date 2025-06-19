# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _, Command

_logger = logging.getLogger(__name__)


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    manufacturer_id = fields.Many2one(
        "product.manufacturer",
        "Manufacturer info"
    )
    manufacturer_pref = fields.Char(
        related="manufacturer_id.manufacturer_pref",
        readonly=False,
    )
    manufacturer_pname = fields.Char(
        related="manufacturer_id.manufacturer_pname",
        readonly=False,
    )

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super().create(vals_list)
    #     for supplierinfo_id, values in zip(res, vals_list):
    #         if values.get('manufacturer_id'):
    #             manufacturer_id = supplierinfo_id.manufacturer_id
    #             manufacturer_id.supplierinfo_ids |= supplierinfo_id
    #     return res
    #
    # def write(self, values):
    #     res = super().write(values)
    #     for record in self:
    #         if values.get('manufacturer_id'):
    #             record.manufacturer_id.supplierinfo_ids |= record
    #     return res
