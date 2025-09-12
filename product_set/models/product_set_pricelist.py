# Copyright 2023 BioPrint Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models, api, _, Command


class ProductSetPricelist(models.Model):
    _name = "product.set.pricelist"
    _description = "Product set pricelist"
    _rec_name = "pricelist_id"
    _order = "product_set_id, pricelist_id"

    product_set_id = fields.Many2one("product.set", string="Set", ondelete="cascade")
    pricelist_id = fields.Many2one(
        'product.pricelist',
        'Set Pricelist',
    )
    amount_untaxed = fields.Monetary(
        string="Pricelist Untaxed Amount"
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='pricelist_id.currency_id',
    )
    company_id = fields.Many2one(
        "res.company",
        related="pricelist_id.company_id",
        store=True,
        readonly=True,
    )

    def action_set_price_list(self):
        for record in self:
            if record.pricelist_id != record.product_set_id.pricelist_id:
                record.product_set_id.pricelist_id = record.pricelist_id
                record.product_set_id.action_update_prices()
