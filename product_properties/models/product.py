# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _, Command

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'product.properties.mixin', 'documents.mixin']

    @staticmethod
    def _get_domain_categ_ids():
        return [
            ('applicability', 'in', ['product', 'productoo'])
        ]

    @staticmethod
    def _get_domain_tmpl_categ_ids():
        return [
            ('applicability', 'in', ['template', 'templateoo'])
        ]

    has_category_properties = fields.Boolean(
        compute="_compute_has_category_properties",
        string="Category Has Product properties"
    )

    product_properties_ids = fields.One2many(
        "product.properties",
        "product_id",
        string='Product properties',
        copy=False
    )

    tmpl_product_prop_static_id = fields.Many2one(
        related="product_tmpl_id.product_prop_static_id"
    )

    has_product_properties = fields.Boolean(
        compute="_compute_has_product_properties",
        string="Product has properties"
    )

    tmpl_product_properties_ids = fields.Many2many(
        "product.properties",
        compute="_compute_tmpl_product_properties_ids",
        string='Product template properties'
    )

    properties_category_ids = fields.Many2many(
        'product.properties.category',
        relation="product_prod_prop",
        string='Global Category properties',
        domain=lambda self: self._get_domain_categ_ids()
    )

    tmpl_properties_category_ids = fields.Many2many(
        'product.properties.category',
        relation="product_tmpl_prod_prop",
        string='Base on Category properties',
        domain=lambda self: self._get_domain_tmpl_categ_ids()
    )

    curr_category_ids = fields.Many2many(
        'product.properties.category',
        string='Category properties',
        compute='_compute_curr_category_ids'
    )

    product_count_static_properties = fields.Integer(
        "Count product static properties",
        compute="_compute_count_static_properties"
    )

    def _compute_count_static_properties(self):
        for record in self:
            record.product_count_static_properties = len(self.env['product.properties.static'].search(
                [('object_id', '=', 'product.product,%s' % record.id)]).ids)

    def _compute_has_category_properties(self):
        for record in self:
            if record.product_tmpl_id.categ_id and record.product_tmpl_id.categ_id.product_properties_ids:
                record.has_category_properties = True
            else:
                record.has_category_properties = False

    def _compute_tmpl_product_properties_ids(self):
        for record in self:
            if record.product_tmpl_id:
                record.tmpl_product_properties_ids = record.product_tmpl_id.product_properties_ids

    @api.depends('product_properties_ids')
    def _compute_has_product_properties(self):
        self.has_product_properties = len(self.product_properties_ids.ids) > 0 or len(
            self.tmpl_product_properties_ids.ids) > 0

    def _compute_curr_category_ids(self):
        for record in self:
            category_ids = record.product_properties_ids.mapped('categ_id')
            category_ids |= record.properties_category_ids
            if category_ids:
                record.curr_category_ids = [Command.link(x) for x in category_ids.ids]
            else:
                record.curr_category_ids = False

    @api.onchange('properties_category_ids')
    def _onchange_properties_category_ids(self):
        for product_id in self:
            product_id.product_properties_ids = self.env['product.properties']. \
                _get_default_product_properties_ids(product_id.mapped('properties_category_ids'), product_id)

    @api.onchange('tmpl_properties_category_ids')
    def _onchange_tmpl_category_ids(self):
        for product_id in self:
            product_id.product_tmpl_id.product_properties_ids = self.env['product.properties']. \
                _get_default_product_properties_ids(product_id.mapped('properties_category_ids'),
                                                    product_id.product_tmpl_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('product_prop_static_id') \
                    and 'product_tmpl_id' in vals:
                values = self.env['product.properties.static'].static_property_data(self, vals)
                vals['product_prop_static_id'] = self.env['product.properties.static']. \
                    create(values['product_prop_static_id']).id
        res = super().create(vals_list)
        for product in res:
            # _logger.info("CREATE %s,%d" % ("%s" % product._name, product.id))
            if product.product_prop_static_id:
                product.product_prop_static_id.write({'object_id': "%s,%d" % ("%s" % product._name, product.id)})
        return res

    def write(self, vals):
        res = super().write(vals)
        values = self.env['product.properties.static'].update_static_property_data(vals)
        if values:
            for product_id in self:
                if product_id.product_prop_static_id:
                    product_id.product_prop_static_id.write(values)
                else:
                    values = self.env['product.properties.static'].static_property_data(product_id, vals)
                    product_id.product_prop_static_id = self.env['product.properties.static']. \
                        create(values['product_prop_static_id']).id
        return res

    def unlink(self):
        for record in self:
            self.env['product.properties.static'].search([('object_id', '=', f'product.product,{record.id}')]).unlink()
            self.env['product.properties'].search([('product_id', '=', record.id)]).unlink()
        return super().unlink()

    def action_get_properties(self):
        for product_id in self:
            default = {}
            if product_id.has_product_properties:
                ret = self.env['product.properties']. \
                    _get_default_product_properties_ids(product_id.mapped('properties_category_ids'), product_id,
                                                        default=default)
                product_id.product_properties_ids = ret

    def auto_correct_static(self):
        for record in self:
            # check for integrated
            static_properties = self.env['product.properties.static'].search(
                [('object_id', '=', 'product.product,%s' % record.id)])
            ingnored = self.env['product.properties.static'].ignore_fields()
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
            'domain': ['|', ('object_id', 'in', ['product.product,%s' % x.id for x in self]),
                       ('object_id', 'in', ['product.template,%s' % x.product_tmpl_id.id for x in self])]
        })
        return action

    def set_category_product_properties(self, category_product_properties_ids):
        self.write({
            'properties_category_ids': [Command.set(category_product_properties_ids.ids)],
            'product_properties_ids': self.env['product.properties'].
            _get_default_product_properties_ids(category_product_properties_ids, self)
        })
