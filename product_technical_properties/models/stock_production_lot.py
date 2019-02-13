# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import api, fields, models
from datetime import timedelta

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    technical_properties_tank = fields.Char(related="product_id.product_tmpl_id.technical_properties_msl", string="Value Tank", store=True)
    lot_date = fields.Datetime(string='LOT Date',
        help='This is the date on which the goods with this Serial Number is poduced.')

    @api.onchange('technical_properties_tank', 'lot_date')
    def _onchange_technical_properties_tank(self):
        res = False
        if self.lot_date:
            d = fields.Datetime.from_string(self.lot_date) + timedelta(days=self.env['product.template']._get_life_time(self.technical_properties_tank))
            res = fields.Datetime.to_string(d)
        return {'value': {'life_date': res}}