# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, tools, models, Command

class MBBOpeningWizard(models.TransientModel):
    _name = 'mbb.opening.wizard'
    _description = 'Wizard to open MBB'

    picking_id = fields.Many2one('stock.picking', string='Piking')
    move_line_ids = fields.Many2many('stock.move.line', string='Product Moves')
    opening_lines = fields.One2many(
        'mbb.opening.wizard.line',
        'wizard_id',
        string='Opening lines'
    )
    mbb_opening_date = fields.Datetime(
        string='MBB opening date',
        default=fields.Datetime.now,
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'move_line_ids' in res:
            move_lines = self.env['stock.move.line'].browse(res['move_line_ids'])
            lines = []
            for line in move_lines:
                if line.lot_id:
                    lines.append({
                        'move_line_id': line.id,
                        'lot_id': line.lot_id.id,
                        'product_id': line.product_id.id,
                        'qty_done': line.qty_done,
                        'current_msl_level': line.product_id.moisture_sensitivity_level,
                        'will_open_mbb': False
                    })
            res['opening_lines'] = [Command.create(line) for line in lines]
        return res

    def action_confirm(self):
        """Потвърждаваме промените и затваряме визарда"""
        # Обновяваме статуса на лотовете
        for line in self.opening_lines:
            if line.will_open_mbb:
                line.lot_id.write({
                    'mbb_status': 'opened',
                    'mbb_opening_date': fields.Datetime.now()
                })

                # Записваме подробно съобщение в chatter лентата
                body = f"""
                <p><strong>MBB packaging is open</strong></p>
                <ul>
                    <li>Date: {fields.Datetime.now().strftime('%d.%m.%Y %H:%M')}</li>
                    <li>User: {self.env.user.name}</li>
                    <li>MSL Level: {line.current_msl_level}</li>
                    <li>Picking: {self.picking_id.name if self.picking_id else 'N/A'}</li>
                </ul>
                """

                line.lot_id.message_post(
                    body=body,
                    subject="MBB Opened",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )

        # Продължаваме с валидирането на операцията
        if self.picking_id:
            result = self.picking_id.with_context(skip_mbb_check=True).button_validate()
            if isinstance(result, dict):
                return result

        # Затваряме визарда
        return {'type': 'ir.actions.act_window_close'}
