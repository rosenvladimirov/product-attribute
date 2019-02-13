# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, except_orm

class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    manifacture_ids = fields.Many2many('res.partner', 'supplierinfo_res_partner_rel',
        'supplier_id', 'manifacture_id', string='Manifactures')

