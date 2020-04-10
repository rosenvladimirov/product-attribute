# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_imperial_measures = fields.Boolean(
        'Show Imperial Measures *',
        related='company_id.show_imperial_measures',
        help='Show supplemental imperial measures for product and packaging.')
