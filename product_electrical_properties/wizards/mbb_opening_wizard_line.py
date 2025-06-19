# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, tools, models, Command
from odoo.addons.product_electrical_properties.models.product_template import MOISTURE_LEVELS


class MBBOpeningWizardLine(models.TransientModel):
    _name = 'mbb.opening.wizard.line'
    _description = 'MBB opening lines'

    wizard_id = fields.Many2one('mbb.opening.wizard')
    move_line_id = fields.Many2one('stock.move.line', string='Product Moves')
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial Number')
    product_id = fields.Many2one('product.product', string='Product')
    qty_done = fields.Float('Quantity')
    current_msl_level = fields.Selection(
        MOISTURE_LEVELS,
        string='MSL Level',
        readonly=True
    )
    will_open_mbb = fields.Boolean('MBB will open')
