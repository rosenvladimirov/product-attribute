# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, tools, models, Command


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    needs_mbb_check = fields.Boolean('Verification to open MBB', compute='_compute_needs_mbb_check')
    will_open_mbb = fields.Boolean('MBB will open')
    data_code = fields.Char(string='Data Code in transfer')

    @api.depends('lot_id', 'location_id', 'location_dest_id')
    def _compute_needs_mbb_check(self):
        for line in self:
            # Проверяваме дали движението е от запечатан лот и променя местоположението
            line.needs_mbb_check = (
                line.lot_id and
                line.lot_id.mbb_status == 'sealed' and
                line.location_id.usage != line.location_dest_id.usage and
                line.product_id.moisture_sensitivity_level != '1'
            )

    def _prepare_new_lot_vals(self):
        vals = super()._prepare_new_lot_vals()
        if self.data_code:
            vals['data_code'] = self.data_code
        return vals
