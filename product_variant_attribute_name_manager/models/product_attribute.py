# Copyright 2025 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    short_name = fields.Char(
        string="Short Name",
        help="Short name to be displayed on the product variant name. "
        "If not set, the attribute name will be used.",
    )
