odoo.define('product_attribute_image.website_sale', function(require) {
"use strict";

    require('website_sale.website_sale');

    $('.oe_website_sale').each(function () {
         var oe_website_sale = this;

        // hightlight selected image
        $('.css_attribute_image input', oe_website_sale).on('change', function () {
            $('.css_attribute_image').removeClass("active");
            $('.css_attribute_image:has(input:checked)').addClass("active");
        });
    });
});
