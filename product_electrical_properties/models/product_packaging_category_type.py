# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductPackagingCategoryType(models.Model):
    _name = "product.packaging.category.type"
    _description = "Category Types of packages"
    _order = 'code, name'

    name = fields.Char(
        'Category Name',
        required=True,
        copy=False,
        translate=True,
        index=True
    )
    code = fields.Char(
        'Category Code',
        required=True,
        copy=False,
        index=True
    )
    volume_type = fields.Selection([
        ('cube', 'Width/Length/Height'),
        ('reer', 'Diameter/Width/Length/Thickness')
    ],
        string="Category Volume type"
    )

    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for reels in self:
            name = reels.name
            if reels.code:
                name = ' - '.join([reels.code, name])
            result.append((reels.id, name))
        return result
