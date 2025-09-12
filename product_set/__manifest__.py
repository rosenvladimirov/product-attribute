# Copyright 2025 Rosen Vladimirov
# Copyright 2023 BioPrint Ltd.
# Copyright 2015 Anybox
# Copyright 2018 Camptocamp, ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Product set",
    "category": "Sale",
    "license": "AGPL-3",
    "author": "Rosen Vladimirov, Anybox, Odoo Community Association (OCA)",
    "version": "18.0.1.0.0",
    "website": "https://github.com/OCA/product-attribute",
    "depends": [
        "product",
        "stock",
        "sale",
    ],
    "data": [
        "data/product_set_data.xml",
        "security/ir.model.access.csv",
        "security/rule_product_set.xml",
        "views/product_set.xml",
        "views/product_set_line.xml",
        "views/product_pricelist_views.xml",
        "views/product_pricelist_item_views.xml",
        "views/product_category_views.xml",
    ],
    "demo": [
        "demo/product_set.xml",
        "demo/product_set_line.xml"
    ],
    "installable": True,
    'post_init_hook': 'post_init_hook',
}
