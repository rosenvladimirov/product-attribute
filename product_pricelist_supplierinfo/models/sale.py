# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.addons import decimal_precision as dp

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pricelist_base_on = fields.Selection(selection_add=[
        ('supplierinfo', 'Supplier price'),
        ])
    supplierinfo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        domain=[('supplier', '=', True)],
        )
