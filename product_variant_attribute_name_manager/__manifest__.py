# Copyright 2025 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product Variant Attribute Name Manager",
    "summary": "Manage how to display the attributes on the product variant name",
    "version": "18.0.1.0.0",
    "category": "Product",
    "website": "https://github.com/OCA/product-attribute",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "product",
    ],
    "data": [
        "views/product_attribute_value_views.xml",
        "views/product_template_views.xml",
        "views/product_template_attribute_line_views.xml",
    ],
    "installable": True,
    "application": False,
}
