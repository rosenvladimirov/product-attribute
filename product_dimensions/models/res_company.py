# -*- coding: utf-8 -*-
# © 2017 Tobias Zehntner
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    show_imperial_measures = fields.Boolean(
        'Show Imperial Measures',
        help='Show supplemental imperial measures for product and packaging.')

    @api.constrains('show_imperial_measures')
    def compute_imperial_measures(self):
        if self.show_imperial_measures:
            template_ids = self.env['product.template'].search([
                ('type', '!=', 'service')])
            template_ids.update_weight_imp()
            template_ids._compute_volume()

            product_ids = template_ids.mapped('product_variant_ids')
            product_ids.update_weight_imp()
            product_ids._compute_volume()

            package_ids = self.env['product.packaging'].search([])
            package_ids.update_weight_imp()
            package_ids._compute_volume()
