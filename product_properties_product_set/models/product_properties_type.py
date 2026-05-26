#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, tools, _, Command

_logger = logging.getLogger(__name__)


class ProductPropertiesType(models.Model):
    _inherit = "product.properties.type"

    def _get_domain_type_field_model_id(self):
        domain = super(ProductPropertiesType, self)._get_domain_type_field_model_id()
        domain[0][2].append('product.set')
        return domain

    def _get_statistic_prop(self, record):
        prop_lines = super()._get_statistic_prop(record)
        if record._name == 'product.set' and record.product_prop_static_id:
            prop_lines |= record.product_prop_static_id
        return prop_lines
