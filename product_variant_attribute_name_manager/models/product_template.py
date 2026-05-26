# Copyright 2025 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    display_variant_name_with_attributes = fields.Boolean(
        string="Display Variant Name with Attributes",
        default=True,
        help="If checked, the variant name will include the attribute values.",
    )
    display_attribute_name = fields.Boolean(
        string="Display Attribute Name",
        default=False,
        help="If checked, the attribute name will be displayed before the attribute value "
        "in the variant name.",
    )
    variant_name_append_mode = fields.Boolean(
        string="Append Attributes to Existing Name",
        default=False,
        help="If checked, attribute values are appended to the display name "
        "computed by other modules (e.g. default code, seller reference) "
        "instead of rebuilding the variant name from scratch. Useful when "
        "other modules contribute prefixes or suffixes that must be preserved.",
    )

    @api.depends(
        "name",
        "product_variant_ids",
        "product_variant_ids.product_template_attribute_value_ids",
        "attribute_line_ids",
        "attribute_line_ids.value_ids",
        "attribute_line_ids.attribute_id.short_name",
        "attribute_line_ids.value_ids.display_name",
        "attribute_line_ids.display_attribute_name",
        "attribute_line_ids.display_attribute_values",
        "attribute_line_ids.sequence",
        "display_variant_name_with_attributes",
        "display_attribute_name",
        "variant_name_append_mode",
    )
    def _compute_display_name(self):
        # Override to not trigger variant name computation here
        # as it's handled in product.product
        return super()._compute_display_name()
