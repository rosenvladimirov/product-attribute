# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _inherit = 'product.set'

    alt_name = fields.Char('Alternative name', translate=True,
                           help="Please fill the alternative name for this product set")
