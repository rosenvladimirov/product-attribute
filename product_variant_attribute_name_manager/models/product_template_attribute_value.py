# Copyright 2025 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    @api.depends(
        "attribute_line_id.display_attribute_name",
        "attribute_line_id.display_attribute_values",
        "attribute_line_id.attribute_id.short_name",
        "product_attribute_value_id.show_in_variant_name",
        "product_attribute_value_id.name",
        "attribute_id.name",
    )
    def _compute_display_name(self):
        """Compute display name based on configuration."""
        for ptav in self:
            display_parts = []
            
            # Check if we should display attribute values at all
            if not ptav.attribute_line_id.display_attribute_values:
                ptav.display_name = ""
                continue
            
            # Check if we should display the attribute name
            if ptav.attribute_line_id.display_attribute_name:
                attr_name = (
                    ptav.attribute_line_id.attribute_id.short_name
                    or ptav.attribute_line_id.attribute_id.name
                )
                display_parts.append(attr_name)
            
            # Check if the value should be displayed
            if ptav.product_attribute_value_id.show_in_variant_name:
                display_parts.append(ptav.product_attribute_value_id.name)
            
            ptav.display_name = ": ".join(display_parts) if display_parts else ""

    def _get_combination_name(self):
        """Override to use custom display logic."""
        ptavs = self.sorted(lambda x: x.attribute_line_id.sequence)
        combination_name_parts = []
        
        for ptav in ptavs:
            if not ptav.attribute_line_id.display_attribute_values:
                continue
            
            display_parts = []
            
            if ptav.attribute_line_id.display_attribute_name:
                attr_name = (
                    ptav.attribute_line_id.attribute_id.short_name
                    or ptav.attribute_line_id.attribute_id.name
                )
                display_parts.append(attr_name)
            
            if ptav.product_attribute_value_id.show_in_variant_name:
                display_parts.append(ptav.product_attribute_value_id.name)
            
            if display_parts:
                combination_name_parts.append(": ".join(display_parts))
        
        return ", ".join(combination_name_parts)
