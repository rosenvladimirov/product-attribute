# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        # Проверяваме дали има нужда от MBB проверка преди валидиране
        lines_need_check = self.move_line_ids.filtered(lambda l: l.needs_mbb_check)
        if lines_need_check:
            return self.action_confirm_mbb_opening()
        return super().button_validate()

    def action_confirm_mbb_opening(self):
        """Визард за потвърждение на отваряне на MBB"""
        lines_to_confirm = self.move_line_ids.filtered(lambda l: l.needs_mbb_check)
        return {
            'name': 'Confirmation to open MBB',
            'type': 'ir.actions.act_window',
            'res_model': 'mbb.opening.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_move_line_ids': lines_to_confirm.ids,
            }
        }
