# Copyright 2025 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    show_in_variant_name = fields.Boolean(
        string="Show in Variant Name",
        default=True,
        help="If checked, the value name will be displayed in the product variant name.",
    )
