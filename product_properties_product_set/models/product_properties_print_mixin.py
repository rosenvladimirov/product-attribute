#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _, Command

_logger = logging.getLogger(__name__)


class ProductPropertiesPrintMixin(models.AbstractModel):
    _inherit = 'product.properties.print.mixin'

    use_product_set = fields.Selection([
        ('reset', 'All open'),
        ('closed', 'All close'),
        ('expand', 'Show expanded'),
        ('collapse', 'Collapse'),
        ('manual', 'Manual')
    ],
        string="Mode view",
        help='Choice mode view expanded or collapse in product sets',
        default="manual")

    def _get_print_product_set_data(self):
        pass

    @api.depends('use_product_set')
    def toggle_use_product_set(self):
        self.ensure_one()
        use_product_set = {'reset': 'closed', 'closed': 'expand', 'expand': 'manual',  'manual': 'collapse', 'collapse': 'reset'}
        self.use_product_set = use_product_set[self.use_product_set]
        self._get_print_product_set_data()
