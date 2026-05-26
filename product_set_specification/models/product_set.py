# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _inherit = 'product.set'

    specifications = fields.Text('Specification', translate=True, help="Plase fill the specifications for this product set")
