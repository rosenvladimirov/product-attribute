#  Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models


class ProductPropertiesStatic(models.Model):
    _inherit = "product.properties.static"

    def _link_domain(self):
        domain = super(ProductPropertiesStatic, self)._link_domain()
        domain[0][2].append('product.set')
        return domain
