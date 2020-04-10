# Copyright 2017 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons import decimal_precision as dp


class ProductPricelistAdding(models.TransientModel):
    _name = 'product.pricelist.adding'

    item_ids = fields.One2many('product.pricelist.item.add', 'product_tmpl_id', 'Pricelist Items')
    update = fields.Selection([
                        ('add', 'Add new price list on selected product[s]'),
                        ('update', 'Update data in price list on selected product[s]'),
                        ('delete', 'Delet price list for selected product[s]'),
                        ], 'Update pricelists', default='add')

    @api.multi
    def mass_add(self):
        ids = self.env.context.get('active_ids', [])
        for product in self.env['product.template'].browse(ids):
            # set_item_ids = list(set(self.item_ids.ids) - set(product.item_ids.ids))
            item_ids = []
            for item_id in self.item_ids:
                if not any([x.id for x in product.item_ids if x.pricelist_id.id == item_id.pricelist_id.id \
                                                              and x.applied_on == item_id.applied_on \
                                                              and x.min_quantity == item_id.min_quantity \
                                                              and x.date_start == item_id.date_start \
                                                              and x.date_end == item_id.date_end]):
                    item_ids.append((0, False, {
                        'product_tmpl_id': product.id,
                        'pricelist_id': item_id.pricelist_id.id,
                        'fixed_price': item_id.fixed_price,
                        'min_quantity': item_id.min_quantity,
                        'date_start': item_id.date_start,
                        'date_end': item_id.date_end,
                        'applied_on': item_id.applied_on,
                    }))
            product.item_ids = item_ids
        return {"type": "ir.actions.act_window_close", }

    @api.multi
    def mass_update(self):
        ids = self.env.context.get('active_ids', [])
        for item_id in self.item_ids:
            for product in self.env['product.template'].browse(ids):
                for item in product.mapped('item_ids').filtered(lambda item: item.pricelist_id.id == item_id.pricelist_id.id \
                                                                                        and item.applied_on == item_id.applied_on \
                                                                                        and item.min_quantity == item_id.min_quantity \
                                                                                        and item.date_start == item_id.date_start \
                                                                                        and item.date_end == item_id.date_end):
                    item.write({
                        'fixed_price': item_id.fixed_price,
                        'min_quantity': item_id.min_quantity,
                        'date_start': item_id.date_start,
                        'date_end': item_id.date_end,
                        })
        return {"type": "ir.actions.act_window_close", }

    @api.multi
    def mass_delete(self):
        ids = self.env.context.get('active_ids', [])
        for item_id in self.item_ids:
            for product in self.env['product.template'].browse(ids):
                for item in product.mapped('item_ids').filtered(lambda item: item.pricelist_id.id == item_id.pricelist_id.id \
                                                                                        and item.applied_on == item_id.applied_on \
                                                                                        and item.min_quantity == item_id.min_quantity \
                                                                                        and item.date_start == item_id.date_start \
                                                                                        and item.date_end == item_id.date_end):
                    item.unlink()
        return {"type": "ir.actions.act_window_close", }

class ProductPricelistItemAdd(models.TransientModel):
    _name = 'product.pricelist.item.add'

    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template',
        help="Specify a template if this rule only applies to one product template. Keep empty otherwise.")
    product_id = fields.Many2one(
        'product.product', 'Product',
        help="Specify a product if this rule only applies to one product. Keep empty otherwise.")
    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        help="Specify a product category if this rule only applies to products belonging to this category or its children categories. Keep empty otherwise.")
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist')
    compute_price = fields.Selection([
        ('fixed', 'Fix Price'),
        ('percentage', 'Percentage (diapplied_onscount)'),
        ('formula', 'Formula')], default='fixed')
    fixed_price = fields.Float('Fixed Price', digits=dp.get_precision('Product Price'))
    applied_on = fields.Selection([
        ('3_global', 'Global'),
        ('2_product_category', ' Product Category'),
        ('1_product', 'Product'),
        ('0_product_variant', 'Product Variant')], "Apply On",
        default='3_global', required=True,
        help='Pricelist Item applicable on selected option')
    base = fields.Selection([
        ('list_price', 'Public Price'),
        ('standard_price', 'Cost'),
        ('pricelist', 'Other Pricelist')], "Based on",
        default='list_price', required=True,
        help='Base price for computation.\n'
             'Public Price: The base price will be the Sale/public Price.\n'
             'Cost Price : The base price will be the cost price.\n'
             'Other Pricelist : Computation of the base price based on another Pricelist.')
    date_start = fields.Date('Start Date', help="Starting date for the pricelist item validation")
    date_end = fields.Date('End Date', help="Ending valid for the pricelist item validation")
    min_quantity = fields.Integer(
        'Min. Quantity', default=0,
        help="For the rule to apply, bought/sold quantity must be greater "
             "than or equal to the minimum quantity specified in this field.\n"
             "Expressed in the default unit of measure of the product.")
