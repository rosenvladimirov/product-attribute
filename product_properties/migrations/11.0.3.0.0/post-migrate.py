# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.api import Environment, SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("TRUNCATE product_properties, product_properties_product_template_rel, product_product_product_properties_rel, product_properties_product_set_rel, product_properties_cat RESTRICT;")
