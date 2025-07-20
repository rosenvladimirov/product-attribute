#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductPropertiesMixin(models.AbstractModel):
    _name = 'product.properties.mixin'
    _description = "Product properties Mixin"

    # product properties fields

    product_prop_static_id = fields.Many2one("product.properties.static",
                                             'Static properties',
                                             copy=False)
