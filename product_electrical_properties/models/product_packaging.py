# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    def unlink(self):
        for pack in self:
            package_id = self.env['product.packaging.reel'].search([('package_id', '=', pack.id)])
            if package_id:
                package_id.with_context(**dict(self._context, block_unlink=True)).unlink()
        return super().unlink()
