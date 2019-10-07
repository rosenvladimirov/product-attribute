# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    print_properties = fields.One2many('product.properties.print', 'picking_id', 'Print properties')
    use_product_description = fields.Boolean(default=True)
