# Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class Manufacturer(models.Model):
    _name = 'product.manufacturer'
    _description = "Product manufactuerer"

    distributor_id = fields.Many2one('res.partner', string='Distributor', index=True, domain=[('supplier', '=', True)])
    manufacturer = fields.Many2one(
        comodel_name='res.partner', string='Manufacturer',
    )
    manufacturer_pname = fields.Char(string='Manuf. Product Name')
    manufacturer_pref = fields.Char(string='Manuf. Product Code')
    manufacturer_purl = fields.Char(string='Manuf. Product URL')
    active = fields.Boolean(default=True)
