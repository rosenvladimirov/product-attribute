# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    type = fields.Selection(selection_add=[('image', 'Small image')])

class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the attribute, limited to 1024x1024px.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of the attribite. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    image_medium = fields.Binary("Medium-sized image", attachment=True,
        help="Medium-sized image of this attribute. It is automatically "\
             "resized as a 128x128px image, with aspect ratio preserved. "\
             "Use this field in form views or some kanban views.")

    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        return super(ProductAttributeValue, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(ProductAttributeValue, self).write(vals)
