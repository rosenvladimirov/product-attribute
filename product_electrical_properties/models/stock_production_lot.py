# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import api, fields, models
from datetime import timedelta

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    electrical_properties_msl = fields.Char(related="product_id.product_tmpl_id.electrical_properties_msl", string="Value MSL", store=True)
    lot_date = fields.Datetime(string='LOT Date',
        help='This is the date on which the goods with this Serial Number is poduced.')

    @api.onchange('electrical_properties_msl', 'lot_date')
    def _onchange_electrical_properties_msl(self):
        res = False
        if self.lot_date:
            d = fields.Datetime.from_string(self.lot_date) + timedelta(days=self.env['product.template']._get_life_time(self.electrical_properties_msl))
            res = fields.Datetime.to_string(d)
        return {'value': {'life_date': res}}