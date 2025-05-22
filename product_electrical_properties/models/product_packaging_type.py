# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductPackagingType(models.Model):
    _name = "product.packaging.type"
    _description = "Type of packages"

    categ_id = fields.Many2one(
        'product.packaging.category.type',
        'Base types of wheels'
    )
    name = fields.Char(
        'Name',
        required=True,
        copy=False,
        related="categ_id.name",
        store=True,
        translate=True,
        readonly=False,
    )
    code = fields.Char(
        'Code',
        required=True,
        copy=False,
        related="categ_id.code",
        store=True,
        readonly = False,
    )
    volume_type = fields.Selection(
        string="Volume type",
        related="categ_id.volume_type",
        readonly=False,
    )
    qty = fields.Float('Quantity per Package', help="The total number of products you can have per box package.")
    active = fields.Boolean('Active', default=True, help="If unchecked, it will allow you to hide the package without removing it.")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name of the package type must be unique !'),
        ('code_uniq', 'unique (code)', 'The code of the package type must be unique !')
    ]
