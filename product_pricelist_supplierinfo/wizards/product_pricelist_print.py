# Copyright 2017 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

class ProductPricelistPrint(models.TransientModel):
    _inherit = 'product.pricelist.print'

    base_on = fields.Selection(selection_add=[
        ('supplierinfo', 'Supplier price')
        ])

    supplierinfo_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Supplier',
        domain='_get_supplierinfo_domain'
    )
    supplier_count = fields.Integer(
        compute='_compute_supplier_count'
    )

    def _get_supplierinfo_domain(self):
        if self.partner_ids:
            suppliers = self.env['product.supplierinfo'].search([
                ('name', '=', self.partner_ids.ids),
                '|',
                ('product_tmpl_id', 'in', self.product_tmpl_ids.ids),
                ('product_id', 'in', self.product_ids.ids)])
        else:
            suppliers = self.env['product.supplierinfo'].search([
                '|',
                ('product_tmpl_id', 'in', self.product_tmpl_ids.ids),
                ('product_id', 'in', self.product_ids.ids)])
        return [('id', 'in', suppliers.ids)]

    @api.multi
    @api.depends('supplierinfo_ids')
    def _compute_supplier_count(self):
        for record in self:
            self.supplier_count = len(record.supplierinfo_ids)

    @api.model
    def default_get(self, fields):
        res = super(ProductPricelistPrint, self).default_get(fields)
        if self.env.context.get('active_model') == 'product.supplierinfo':
                res['supplierinfo_ids'] = [(6, 0, active_ids)]
                product_ids = []
                product_tmpl_ids = []
                for product in self.env['product.supplierinfo'].browse(active_ids):
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
