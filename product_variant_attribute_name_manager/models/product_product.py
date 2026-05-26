# Copyright 2025 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.depends(
        "product_template_attribute_value_ids",
        "product_template_attribute_value_ids.name",
        "product_template_attribute_value_ids.product_attribute_value_id",
        "product_template_attribute_value_ids.attribute_line_id",
        "product_template_attribute_value_ids.attribute_line_id.sequence",
        "product_template_attribute_value_ids.attribute_line_id.display_attribute_name",
        "product_template_attribute_value_ids.attribute_line_id.display_attribute_values",
        "product_template_attribute_value_ids.attribute_line_id.attribute_id.short_name",
        "product_template_attribute_value_ids.product_attribute_value_id.show_in_variant_name",
        "product_tmpl_id.display_variant_name_with_attributes",
        "product_tmpl_id.display_attribute_name",
        "product_tmpl_id.variant_name_append_mode",
        "product_tmpl_id.name",
    )
    @api.depends_context(
        "display_default_code",
        "seller_id",
        "company_id",
        "lang",
        "partner_id",
    )
    def _compute_display_name(self):
        """Override to compute variant name with custom attribute display."""
        for product in self:
            if not product.product_tmpl_id.display_variant_name_with_attributes:
                # Use standard behavior if custom naming is disabled
                super(ProductProduct, product)._compute_display_name()
                continue

            if product.product_tmpl_id.variant_name_append_mode:
                # Append mode: preserve display_name produced by super()
                # (which may include default_code, seller code, or other
                # prefixes contributed by third-party modules) and only
                # add the attribute values that are not already visible.
                super(ProductProduct, product)._compute_display_name()
                product._append_missing_attributes_to_display_name()
                continue

            # Rewrite mode: build the variant name from scratch using our
            # custom logic — ignores any display_name contributions from
            # other modules.
            variant_name = product._get_combination_name()

            if variant_name:
                product.display_name = f"{product.product_tmpl_id.name} ({variant_name})"
            else:
                product.display_name = product.product_tmpl_id.name

    def _append_missing_attributes_to_display_name(self):
        """Append attribute values that are not already present in
        ``display_name`` to the end of the name, reusing the existing
        parenthesis block when possible.

        Examples:
          ``[REF01] Template (XL)`` + missing ``Red``  →
              ``[REF01] Template (XL, Red)``
          ``[REF01] Template`` + missing ``XL``, ``Red`` →
              ``[REF01] Template (XL, Red)``

        Honours the same per-line / per-value / per-template flags as the
        rewrite mode: ``display_attribute_values``, ``show_in_variant_name``,
        and ``display_attribute_name``.
        """
        self.ensure_one()
        if not self.product_template_attribute_value_ids:
            return

        current = self.display_name or ""
        ptavs = self.product_template_attribute_value_ids.sorted(
            lambda x: x.attribute_line_id.sequence
        )

        missing = []
        for ptav in ptavs:
            if not ptav.attribute_line_id.display_attribute_values:
                continue
            if not ptav.product_attribute_value_id.show_in_variant_name:
                continue

            value_name = ptav.product_attribute_value_id.name
            if not value_name or value_name in current:
                continue

            if (
                ptav.attribute_line_id.display_attribute_name
                or self.product_tmpl_id.display_attribute_name
            ):
                attr_name = (
                    ptav.attribute_line_id.attribute_id.short_name
                    or ptav.attribute_line_id.attribute_id.name
                )
                missing.append(f"{attr_name}: {value_name}")
            else:
                missing.append(value_name)

        if not missing:
            return

        extra = ", ".join(missing)
        if current.endswith(")"):
            self.display_name = f"{current[:-1]}, {extra})"
        else:
            self.display_name = f"{current} ({extra})"

    def _get_combination_name(self):
        """Get combination name with custom display logic."""
        self.ensure_one()
        
        if not self.product_template_attribute_value_ids:
            return ""
        
        # Sort by attribute line sequence
        ptavs = self.product_template_attribute_value_ids.sorted(
            lambda x: x.attribute_line_id.sequence
        )
        
        combination_name_parts = []
        
        for ptav in ptavs:
            # Skip if attribute values should not be displayed
            if not ptav.attribute_line_id.display_attribute_values:
                continue
            
            display_parts = []
            
            # Add attribute name if configured
            if (
                ptav.attribute_line_id.display_attribute_name
                or self.product_tmpl_id.display_attribute_name
            ):
                attr_name = (
                    ptav.attribute_line_id.attribute_id.short_name
                    or ptav.attribute_line_id.attribute_id.name
                )
                display_parts.append(attr_name)
            
            # Add attribute value if configured
            if ptav.product_attribute_value_id.show_in_variant_name:
                display_parts.append(ptav.product_attribute_value_id.name)
            
            # Join parts and add to combination
            if display_parts:
                combination_name_parts.append(": ".join(display_parts))
        
        return ", ".join(combination_name_parts)
