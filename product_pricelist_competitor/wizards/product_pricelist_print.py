# Copyright 2017 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ProductPricelistPrint(models.TransientModel):
    _inherit = 'product.pricelist.print'

    def _get_competitorinfo_domain(self):
        if self.product_tmpl_ids or self.product_ids:
            competitors = self.env['product.competitorinfo'].search([
                '|',
                ('product_tmpl_id', 'in', self.product_tmpl_ids.ids),
                ('product_id', 'in', self.product_ids.ids)])
        else:
            return [('name.competitor', '=', True)]
        return [('id', 'in', competitors.ids)]

    base_on = fields.Selection(selection_add=[
        ('competitorinfo', 'Competitor price')
        ])

    competitorinfo_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Competitor',
        domain=_get_competitorinfo_domain
    )
    competitor_count = fields.Integer(
        compute='_compute_competitor_count'
    )

    @api.multi
    @api.depends('competitorinfo_ids')
    def _compute_competitor_count(self):
        for record in self:
            self.competitor_count = len(record.competitorinfo_ids)

    @api.model
    def default_get(self, fields):
        res = super(ProductPricelistPrint, self).default_get(fields)
        if self.env.context.get('active_model') == 'product.competitorinfo':
                res['supplierinfo_ids'] = [(6, 0, active_ids)]
                product_ids = []
                product_tmpl_ids = []
                for product in self.env['product.competitorinfo'].browse(active_ids):
                    if product.product_id:
                        product_ids.append(product.id)
                    elif not product.product_id and product.product_tmpl_id:
                        product_tmpl_ids.append(product.product_tmpl_id.id)
                if product_ids:
                    res['product_ids'] = [
                        (6, 0, product_ids)]
                if product_tmpl_ids:
                    res['product_tmpl_ids'] = [
                        (6, 0, product_tmpl_ids)]
        return res
