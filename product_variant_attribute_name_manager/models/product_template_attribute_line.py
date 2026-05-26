# Copyright 2025 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplateAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    display_attribute_name = fields.Boolean(
        string="Display Attribute Name",
        default=False,
        help="If checked, the attribute name will be displayed before the attribute value "
        "in the variant name.",
    )
    display_attribute_values = fields.Boolean(
        string="Display Attribute Values",
        default=True,
        help="If checked, the attribute values will be displayed in the variant name.",
    )
