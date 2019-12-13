# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HSCode(models.Model):
    _inherit = "hs.code"

    taric_code = fields.Char(
        required=True,
        help="Taric Code used for the EU customs Import/Export declaration. "
        "The EU Taric code starts with the 6 digits of the H.S. and often "
        "has a few additional digits to extend the H.S. code.")

    @api.onchange('taric_code')
    def taric_code_change(self):
        if self.taric_code and self.hs_code and self.taric_code[:6] != self.hs_code:
            raise ValidationError(_('The taric code is not correct (%s != %s). Please check local code or H.S. Code.' % (self.taric_code, self.hs_code)))
        elif self.taric_code and not self.hs_code:
            self.hs_code = self.taric_code[:6]
        if self.taric_code and not self.local_code:
            self.local_code = self.taric_code[:8]
