# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.tools.misc import format_date

import logging
_logger = logging.getLogger(__name__)


class QuantPackage(models.Model):
    _inherit = "stock.quant.package"

    partner_info_id = fields.Many2one(
        'res.partner', 'Partner Info', compute='_compute_partner_info', search='_search_partner',
        index=True, readonly=True)

    def _compute_partner_info(self):
        for package in self:
            move_line = self.env['stock.move.line'].search([('result_package_id', '=', package.id)], limit=1)
            if move_line:
                picking = move_line.move_id.picking_id
                if picking and picking.partner_id:
                    package.partner_info_id = picking.partner_id

    def _format_date(self, value, lang_code=False, date_format=False):
        return format_date(self.env, value, lang_code=lang_code, date_format=date_format)
