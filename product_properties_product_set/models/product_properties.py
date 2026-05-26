#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _, Command

_logger = logging.getLogger(__name__)


class ProductProperties(models.Model):
    _inherit = "product.properties"

    product_set_id = fields.Many2one('product.set', string='Product set', index=True)

    def _get_model_obj_id(self):
        if self.type_field_model == 'product.set':
            return self.product_set_id.id
        return super()._get_model_obj_id()
