# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, Command

import logging

from odoo.addons.spreadsheet.tests.validate_spreadsheet_data import domain_fields

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ['product.template', 'product.properties.mixin']

    def _get_domain_categ_ids(self):
        return [
            ('applicability', 'in', ['template', 'templateoo']),
        ]

    has_category_properties = fields.Boolean(compute="_compute_has_category_properties",
                                             string="Category Has Product properties")
    product_properties_ids = fields.One2many("product.properties", "product_tmpl_id",
                                             string='Product properties',
                                             domain=[('product_id', '=', False)], copy=False)
    product_prop_static_v_id = fields.Many2one('product.product',
                                               'Static data for variant',
                                               compute='_compute_product_static_variant_id')

    has_product_properties = fields.Boolean("Product has properties",
                                            compute="_compute_has_product_properties")

    count_static_properties = fields.Integer("Count static properties",
                                             compute="_compute_count_static_properties")

    properties_category_ids = fields.Many2many('product.properties.category', relation="product_tmpl_prop",
                                               string='Global Category properties',
                                               domain=lambda self: self._get_domain_categ_ids())
    curr_category_ids = fields.Many2many('product.properties.category',
                                         string='Category properties',
                                         compute='_compute_curr_category_ids')

    def _compute_count_static_properties(self):
        for record in self:
            record.count_static_properties = len(self.env['product.properties.static'].search(
                [('object_id', '=', 'product.template,%s' % record.id)]).ids)

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

    @api.depends('properties_category_ids')
    def _compute_curr_category_ids(self):
        for record in self:
            curr_category_ids = record.product_properties_ids.mapped('categ_id')
            curr_category_ids |= record.properties_category_ids
            if len(curr_category_ids.ids) > 0:
                record.curr_category_ids = [Command.link(x) for x in curr_category_ids.ids]
            else:
                record.curr_category_ids = False
            # _logger.info(f'curr_category_ids: {curr_category_ids}')

    @api.depends('product_variant_ids')
    def _compute_product_static_variant_id(self):
        for record in self:
            record.product_prop_static_v_id = record.product_variant_ids[:1].product_prop_static_id

    @api.onchange('properties_category_ids')
    def _onchange_properties_category_ids(self):
        for product_tmpl_id in self:
            product_tmpl_id.product_properties_ids = self.env['product.properties']. \
                _get_default_product_properties_ids(product_tmpl_id.mapped('properties_category_ids'), product_tmpl_id)
            if product_tmpl_id.product_variant_count > 0:
                applicability = self.env['product.properties.category'].search([('applicability', '=', 'product')])
                for product in product_tmpl_id.product_variant_ids:
                    if len(product.product_properties_ids.ids) == 0:
                        product.properties_category_ids = [Command.set(applicability.ids)]

    @api.model_create_multi
    def create(self, vals_list):
        static_ids = self.env['product.properties.static'].static_property_fields()
        for vals in vals_list:
            if not vals.get('product_prop_static_id') \
                    and not vals.get('attribute_line_ids') \
                    and any([x in vals for x in static_ids]):
                values = self.env['product.properties.static'].static_property_data(self, vals)
                vals['product_prop_static_id'] = self.env['product.properties.static']. \
                    create(values['product_prop_static_id']).id

        # _logger.info("VALS %s" % vals_list)
        res = super(ProductTemplate, self).create(vals_list)
        for product_tmpl_id, vals in zip(res, vals_list):
            if product_tmpl_id.product_prop_static_id:
                product_tmpl_id.product_prop_static_id.object_id = "%s,%d" % (res._name, product_tmpl_id.id)
        return res

    def write(self, vals):
        update_values = self.env['product.properties.static'].update_static_property_data(vals)
        for line in update_values.keys():
            if vals.get(line):
                del vals[line]
            if vals.get(f'v{line}'):
                del vals[f'v{line}']

        static_ids = self.env['product.properties.static'].static_property_fields()
        old_res = {}

        for line in self:
            old_res[line] = len(line.attribute_line_ids) > 0
        res = super().write(vals)
        for product_tmpl_id in self:
            if any([x in vals for x in static_ids]):
                if (not old_res[product_tmpl_id]
                    and len(product_tmpl_id.attribute_line_ids) > 0) \
                    or (not product_tmpl_id.product_prop_static_id
                        and len(product_tmpl_id.attribute_line_ids) > 0):
                    values = self.env['product.properties.static'].static_property_data(self, vals)
                    update_values = values['product_prop_static_id']
                    product_prop_static_id = self.env['product.properties.static']. \
                        create(values['product_prop_static_id'])
                    product_tmpl_id.write({
                        'product_prop_static_id': product_prop_static_id.id
                    })
                elif old_res[product_tmpl_id] and len(product_tmpl_id.attribute_line_ids) == 0:
                    product_tmpl_id.product_prop_static_id = False
            if product_tmpl_id.product_prop_static_id and update_values:
                product_prop_static_id = self.env['product.properties.static']. \
                    browse(product_tmpl_id.product_prop_static_id.id)
                _logger.info("Properties static %s" % update_values)
                product_prop_static_id.write(update_values)
        _logger.info("\nHas static_ids: %s\nupdate_values: %s\nvals: %s" % (any([x in vals for x in static_ids]), update_values, vals))
        return res

    def unlink(self):
        for record in self:
            self.env['product.properties.static'].search([('object_id', '=', f'product.template,{record.id}')]).unlink()
            self.env['product.properties'].search([('product_tmpl_id', '=', record.id)]).unlink()
        return super().unlink()

    def action_get_properties(self):
        for product_tmpl_id in self:
            default = {}
            if product_tmpl_id.has_category_properties:
                res = self.env['product.properties']. \
                    _get_default_product_properties_ids(product_tmpl_id.mapped('categ_id'),
                                                        product_tmpl_id,
                                                        default=default)
                product_tmpl_id.product_properties_ids = res

    def auto_correct_static(self):
        for record in self:
            ingnored = self.env['product.properties.static'].ignore_fields()
            if len(record.product_variant_ids.ids) > 1 and not record.product_prop_static_id:
                # check for integrated
                for variant in record.product_variant_ids:
                    static_properties = self.env['product.properties.static'].search(
                        [('object_id', '=', 'product.product,%s' % variant.id)])
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
                        variant.product_prop_static_id = static_properties_id
                    else:
                        variant.product_prop_static_id = False

            elif record.product_prop_static_id:
                static_properties = self.env['product.properties.static'].search(
                    [('object_id', '=', 'product.template,%s' % record.id)])
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
            'domain': [('object_id', 'in', ['product.template,%s' % x.id for x in self])]
        })
        return action

    def set_category_product_properties(self, category_product_properties_ids):
        _logger.info(
            f'category_product_properties_ids mapped: {category_product_properties_ids.ids}')
        self.write({
            'properties_category_ids': [Command.set(category_product_properties_ids.ids)],
            'product_properties_ids': self.env['product.properties'].
            _get_default_product_properties_ids(category_product_properties_ids, self),
        })
        if self.product_variant_count > 0:
            applicability = self.env['product.properties.category'].search(
                [('applicability', '=', 'product')])
            if applicability:
                for product in self.product_variant_ids:
                    if len(product.product_properties_ids.ids) == 0:
                        product.write({
                            'properties_category_ids': [Command.set(applicability.ids)],
                            'product_properties_ids': self.env['product.properties'].
                            _get_default_product_properties_ids(applicability, product)
                        })
