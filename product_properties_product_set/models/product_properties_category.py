#  -*- coding: utf-8 -*-
#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import fields, models, _

_logger = logging.getLogger(__name__)


class ProductPropertiesCategory(models.Model):
    _inherit = "product.properties.category"

    applicability = fields.Selection(selection_add=[
        ('product_set', 'Product set')
    ], ondelete={'product_set': 'set default'})
