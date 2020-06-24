# Copyright 2017 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Product Pricelist Direct Print with Product Properties",
    "summary": "Print price list from menu option, product templates, "
               "products variants or price lists with product properties ",
    "version": "11.0.1.1.0",
    "category": "Product",
    "website": "https://www.github.com/rosenvladimirov/product-attribute",
    "author": "Rosen Vladimirov, BioPrint Ltd.",
    "license": "AGPL-3",
    "depends": [
        "product_pricelist_direct_print",
        "product_properties",
        'sale_product_set_pricelist_direct_print',
    ],
    "data": [
        'views/product_properties_pricelist.xml',
        'views/report_product_pricelist.xml',
        'wizards/product_pricelist_print_view.xml',
    ],
}
