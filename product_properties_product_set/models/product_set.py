#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import fields, models, api, _, Command

_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _name = "product.set"
    _inherit = ["product.set", "product.properties.mixin"]

    def _get_domain_categ_ids(self):
        return [
            ('applicability', '=', 'product_set')
        ]

    has_product_properties = fields.Boolean("Product has properties",
                                            compute="_compute_has_product_properties")

    product_properties_ids = fields.One2many("product.properties", "product_set_id",
                                             string='Product properties',
                                             domain=[('product_tmpl_id', '=', False)], copy=False)

    has_category_properties = fields.Boolean(compute="_compute_has_category_properties",
                                             string="Category Has Product properties")
    properties_category_ids = fields.Many2many('product.properties.category', relation="product_set_prop",
                                               string='Global Category properties',
                                               domain=lambda self: self._get_domain_categ_ids())

    curr_category_ids = fields.Many2many('product.properties.category',
                                         string='Category properties',
                                         compute='_compute_curr_category_ids')
    count_static_properties = fields.Integer("Count static properties",
                                             compute="_compute_count_static_properties")


    @api.depends('product_properties_ids')
    def _compute_has_product_properties(self):
        self.ensure_one()
        self.has_product_properties = len(self.product_properties_ids.ids) > 0 or False

    def _compute_has_category_properties(self):
        for record in self:
            if record.categ_id and record.categ_id.product_properties_ids:
                record.has_category_properties = True
            else:
                record.has_category_properties = False

    @api.onchange('properties_category_ids')
    def _onchange_properties_category_ids(self):
        for product_set_id in self:
            product_set_id.product_properties_ids = self.env['product.properties']. \
                _get_default_product_properties_ids(product_set_id.mapped('properties_category_ids'), product_set_id)

    def _compute_curr_category_ids(self):
        for record in self:
            curr_category_ids = record.product_properties_ids.mapped('categ_id')
            if len(curr_category_ids.ids) > 0:
                record.curr_category_ids = [Command.link(x) for x in curr_category_ids.ids]
            else:
                record.curr_category_ids = False

    def _compute_count_static_properties(self):
        for record in self:
            record.count_static_properties = len(self.env['product.properties.static'].search(
                [('object_id', '=', 'product.set,%s' % record.id)]).ids)

    def auto_correct_static(self):
        for record in self:
            ingnored = self.env['product.properties.static'].ignore_fields()

            if record.product_prop_static_id:
                static_properties = self.env['product.properties.static'].search(
                    [('object_id', '=', 'product.set,%s' % record.id)])
                static_properties_id = static_properties and static_properties[0] or False
                maximal = 0
                for line in static_properties:
                    current = 0
                    for field in line._fields:
                        if field not in ingnored and getattr(line, field):
                            if current >= max(maximal, current):
                                maximal = max(maximal, current)
                                static_properties_id = line
                            current += 1
                # _logger.info("STATIC ID %s" % static_properties_id)
                if static_properties_id:
                    record.product_prop_static_id = static_properties_id
                else:
                    record.product_prop_static_id = False

    def view_static_properties(self):
        action = self.env.ref('product_properties.product_properties_static_action').read()[0]
        action.update({
            'domain': [('object_id', 'in', ['product.set,%s' % x.id for x in self])]
        })
        return action

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('product_prop_static_id') \
                    and 'product_tmpl_id' in vals:
                values = self.env['product.properties.static'].static_property_data(self, vals)
                vals['product_prop_static_id'] = self.env['product.properties.static'].\
                    create(values['product_prop_static_id']).id
        res = super().create(vals_list)
        for product_set in res:
            if product_set.product_prop_static_id:
                product_set.product_prop_static_id.write({'object_id': "%s,%d" % ("%s" % product_set._name, product_set.id)})
        return res

    def write(self, vals):
        res = super().write(vals)
        values = self.env['product.properties.static'].update_static_property_data(vals)
        if values:
            for product_set_id in self:
                if product_set_id.product_prop_static_id:
                    product_set_id.product_prop_static_id.write(values)
                else:
                    values = self.env['product.properties.static'].static_property_data(self, vals)
                    # _logger.info("VALUES %s" % values)
                    product_set_id.product_prop_static_id = self.env['product.properties.static']. \
                        create(values['product_prop_static_id']).id
        return res

    def unlink(self):
        self.env['product.properties.static'].search([('object_id', '=', f'product.set,{self.id}')]).unlink()
        self.env['product.properties'].search([('product_set_id', '=', self.id)]).unlink()
        return super().unlink()
