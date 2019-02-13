# -*- coding: utf-8 -*-
# © 2017 Tobias Zehntner
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Add precision to volume via decimal_precision addon
    volume = fields.Float(digits=dp.get_precision('Stock Volume'),
                          compute='_compute_volume', readonly=True)

    # Remove compute from existing weight field
    weight = fields.Float(compute=False, inverse=False)

    # Weight in grams
    weight_g = fields.Float('Weight in gram',
                            digits=dp.get_precision('Stock Weight Gram'),
                            help='The weight in gram not including '
                                 'packaging etc')
    weight_display = fields.Selection([('kg', 'kg'), ('g', 'g')],
                                      string='Weight Display Unit',
                                      default='kg')

    # Dimension fields
    length = fields.Float('Length',
                          digits=dp.get_precision('Stock Dimension'),
                          help='The length in cm, not including packaging etc')
    width = fields.Float('Width', digits=dp.get_precision('Stock Dimension'),
                         help='The width in cm, not including packaging etc')
    height = fields.Float('Height',
                          digits=dp.get_precision('Stock Dimension'),
                          help='The height in cm, not including packaging etc')

    # Imperial measures
    show_imperial = fields.Boolean('Show Imperial Measures',
                                   compute='_compute_show_imperial')
    volume_gal = fields.Float('Volume (Gal)',
                              digits=dp.get_precision('Stock Volume Gallon'),
                              readonly=True,
                              help='The Volume in imperial Gallons')
    weight_lb = fields.Float('Weight (Lb)',
                             digits=dp.get_precision('Stock Weight Pound'),
                             readonly=True,
                             help='The weight in pounds not including '
                                  'packaging etc')
    weight_oz = fields.Float('Weight (Oz)',
                             digits=dp.get_precision('Stock Weight Ounce'),
                             readonly=True,
                             help='The weight in ounces not including '
                                  'packaging etc')
    length_in = fields.Float('Length (In)',
                             digits=dp.get_precision('Stock Dimension'),
                             compute='update_dimension_imp',
                             help='The length in inch, not including '
                                  'packaging etc')
    width_in = fields.Float('Width (In)',
                            digits=dp.get_precision('Stock Dimension'),
                            compute='update_dimension_imp',
                            help='The width in inch, not including '
                                 'packaging etc')
    height_in = fields.Float('Height (In)',
                             digits=dp.get_precision('Stock Dimension'),
                             compute='update_dimension_imp',
                             help='The height in inch, not including '
                                  'packaging etc')

    @api.multi
    def _compute_show_imperial(self):
        show_imp = self.env.user.company_id.show_imperial_measures
        for template in self:
            template.show_imperial = show_imp

    @api.multi
    @api.onchange('weight_display')
    def get_weight(self):
        """
        Convert kg to g and vice versa
        """
        for template in self:
            if template.weight_display == 'g':
                template.weight_g = template.weight * 1000
            else:
                template.weight = template.weight_g / 1000

    @api.multi
    @api.constrains('weight')
    def update_weight_g(self):
        """
        If weight in kilogram gets changed, update weight in grams
        """
        for template in self:
            if not template.weight_g == (template.weight * 1000):
                template.weight_g = template.weight * 1000

    @api.multi
    @api.constrains('weight_g')
    def update_weight_kg(self):
        """
        If weight in gram gets changed, update weight in kilograms
        """
        for template in self:
            if not template.weight == (template.weight_g / 1000):
                template.weight = template.weight_g / 1000

    @api.multi
    @api.onchange('weight')
    @api.constrains('weight')
    def update_weight_imp(self):
        """
        Compute imperial units on changing weight
        """
        for template in self:
            oz = template.weight * 35.27396195
            template.weight_lb = int(oz / 16)
            template.weight_oz = oz % 16

    @api.multi
    @api.depends('length', 'width', 'height')
    @api.onchange('length', 'width', 'height')
    def _compute_volume(self):
        """
        Compute volume from dimensions in cubic meters
        """
        for template in self.filtered(
                lambda t: t.length and t.width and t.height):
            # get volume in m3
            volume = (template.length / 100.0) * (template.width / 100.0) * (
                    template.height / 100.0)
            template.volume = volume
            template.volume_gal = volume * 219.96924829909

    @api.multi
    @api.onchange('length', 'width', 'height')
    @api.depends('length', 'width', 'height')
    def update_dimension_imp(self):
        """
        Compute imperial units on changing dimensions
        """
        for template in self:
            template.length_in = template.length * 0.3937007874
            template.width_in = template.width * 0.3937007874
            template.height_in = template.height * 0.3937007874

    @api.multi
    def write(self, vals):
        """
        Sync dimensions with variants if they have none set or if they were
        in sync with the template before the write()
        """
        res = super(ProductTemplate, self).write(vals)
        keys = ['length', 'width', 'height', 'weight', 'weight_display']
        if 'product_variant_ids' in vals and len(template.product_variant_ids) > 1:
            # collect exist products
            exist_variants = template.product_variant_ids.filtered(lambda r: any([r.length, r.width, r.height]))
            _logger.info("Start variants __________ %s" % exist_variants)
            for variant in template.product_variant_ids:
                # If variant has none set or it was in sync with
                # template before write(), sync it anew
                if any(['length', 'width', 'height']) not in vals and \
                        not any([variant.length, variant.width, variant.height]):
                    for exist_variant in exist_variants:
                        for x in exist_variant.attribute_value_ids:
                            _logger.info("Variant demensions _________________ %s:%s" % (x, variant.attribute_value_ids))
                            if x.id in variant.attribute_value_ids:
                                variant.write({
                                        'length': vals.get('length') or x.length,
                                        'width': vals.get('width') or x.width,
                                        'height': vals.get('height') or x.height,
                                    })

        if any(key in vals for key in keys):
            for template in self:
                if len(template.product_variant_ids) == 1:
                    # If only one variant and it is different, sync it
                    variant = template.product_variant_ids
                    if ('length' in vals and vals['length'] != variant.length) \
                            or ('width' in vals and vals[
                                'width'] != variant.width) \
                            or ('weight' in vals and vals[
                                'weight'] != variant.weight) \
                            or ('weight_display' in vals and vals[
                                'weight_display'] != variant.weight_display):
                        variant.write({
                            'length': vals.get('length') or template.length,
                            'width': vals.get('width') or template.width,
                            'height': vals.get('height') or template.height,
                            'weight': vals.get('weight') or template.weight,
                            'weight_display': vals.get('weight_display')
                                              or template.weight_display
                        })

                else:
                    for variant in template.product_variant_ids:
                        # If variant has none set or it was in sync with
                        # template before write(), sync it anew
                        if any(['length', 'width', 'height']) in vals and \
                                (not any([variant.length, variant.width,
                                          variant.height])
                                         or (variant.length == template.length
                                             and variant.width == template.width
                                             and variant.height == template.height)):
                            variant.write({
                                'length': vals.get('length') or template.length,
                                'width': vals.get('width') or template.width,
                                'height': vals.get('height') or template.height,
                            })

                        if 'weight' in vals \
                                and (not variant.weight
                                     or (variant.weight == template.weight
                                         and vals['weight'] != variant.weight)):
                            variant.weight = vals['weight']
                        if 'weight_display' in vals \
                                and template.weight_display \
                                        != variant.weight_display:
                            # If weight display preference changes on template
                            # we change it on all variants
                            variant.weight_display = vals['weight_display']

        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Add precision to volume via decimal_precision addon
    volume = fields.Float(digits=dp.get_precision('Stock Volume'),
                          compute='_compute_volume')

    # Weight in grams
    weight_g = fields.Float('Weight in gram',
                            digits=dp.get_precision('Stock Weight Gram'),
                            help='The weight in gram not including '
                                 'packaging etc')
    weight_display = fields.Selection([('kg', 'kg'), ('g', 'g')],
                                      string='Weight Display Unit',
                                      default='kg')

    # Dimension fields
    length = fields.Float('Length',
                          digits=dp.get_precision('Stock Dimension'),
                          help='The length in cm, not including packaging etc')
    width = fields.Float('Width', digits=dp.get_precision('Stock Dimension'),
                         help='The width in cm, not including packaging etc')
    height = fields.Float('Height',
                          digits=dp.get_precision('Stock Dimension'),
                          help='The height in cm, not including packaging etc')

    # Imperial measures
    volume_gal = fields.Float('Volume (Gal)',
                              digits=dp.get_precision('Stock Volume Gallon'),
                              readonly=True,
                              help='The Volume in imperial Gallons')
    weight_lb = fields.Float('Weight (Lb)',
                             digits=dp.get_precision('Stock Weight Pound'),
                             readonly=True,
                             help='The weight in pounds not including '
                                  'packaging etc')
    weight_oz = fields.Float('Weight (Oz)',
                             digits=dp.get_precision('Stock Weight Ounce'),
                             readonly=True,
                             help='The weight in ounces not including '
                                  'packaging etc')
    length_in = fields.Float('Length (In)',
                             digits=dp.get_precision('Stock Dimension'),
                             compute='update_dimension_imp',
                             help='The length in inch, not including '
                                  'packaging etc')
    width_in = fields.Float('Width (In)',
                            digits=dp.get_precision('Stock Dimension'),
                            compute='update_dimension_imp',
                            help='The width in inch, not including '
                                 'packaging etc')
    height_in = fields.Float('Height (In)',
                             digits=dp.get_precision('Stock Dimension'),
                             compute='update_dimension_imp',
                             help='The height in inch, not including '
                                  'packaging etc')

    @api.model
    def create(self, vals):
        """
        On variant creation, copy template measurements
        """
        res = super(ProductProduct, self).create(vals)
        for variant in res:
            template = variant.product_tmpl_id
            variant.write({
                'length': template.length,
                'width': template.width,
                'height': template.height,
                'weight': template.weight,
                'weight_display': template.weight_display
            })
        return res

    @api.multi
    @api.constrains('length', 'width', 'height', 'weight')
    def update_tmpl_dimensions(self):
        """
        If only one variant and template is different, update template
        """
        for variant in self:
            template = variant.product_tmpl_id
            if len(template.product_variant_ids) == 1 \
                    and (variant.length != template.length
                         or variant.width != template.width
                         or variant.height != template.height
                         or variant.weight != template.weight):
                template.write({
                    'length': variant.length,
                    'width': variant.width,
                    'height': variant.height,
                    'weight': variant.weight
                })

    @api.multi
    @api.onchange('weight_display')
    def get_weight(self):
        """
        Convert kg to g and vice versa
        """
        for variant in self:
            if variant.weight_display == 'g':
                variant.weight_g = variant.weight * 1000
            else:
                variant.weight = variant.weight_g / 1000

    @api.multi
    @api.constrains('weight')
    def update_weight_g(self):
        """
        If weight in kilogram gets changed, update weight in grams
        """
        for variant in self:
            if not variant.weight_g == (variant.weight * 1000):
                variant.weight_g = variant.weight * 1000

    @api.multi
    @api.constrains('weight_g')
    def update_weight_kg(self):
        """
        If weight in gram gets changed, update weight in kilograms
        """
        for variant in self:
            if not variant.weight == (variant.weight_g / 1000):
                variant.weight = variant.weight_g / 1000

    @api.multi
    @api.onchange('weight')
    @api.constrains('weight')
    def update_weight_imp(self):
        """
        Compute imperial units on changing weight
        """
        for variant in self:
            oz = variant.weight * 35.27396195
            variant.weight_lb = int(oz / 16)
            variant.weight_oz = oz % 16

    @api.multi
    @api.depends('length', 'width', 'height')
    @api.onchange('length', 'width', 'height')
    def _compute_volume(self):
        """
        Compute volume from dimensions in cubic meters
        """
        for variant in self.filtered(
                lambda v: v.length and v.width and v.height):
            # get volume in m3
            volume = (variant.length / 100.0) * (
                    variant.width / 100.0) * (variant.height / 100.0)
            variant.volume = volume
            variant.volume_gal = volume * 219.96924829909

    @api.multi
    @api.onchange('length', 'width', 'height')
    @api.depends('length', 'width', 'height')
    def update_dimension_imp(self):
        """
        Compute imperial units on changing dimensions
        """
        for variant in self:
            variant.length_in = variant.length * 0.3937007874
            variant.width_in = variant.width * 0.3937007874
            variant.height_in = variant.height * 0.3937007874


class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    # Add volume, weight and dimensions to packaging
    weight = fields.Float('Weight',
                          digits=dp.get_precision('Stock Weight'),
                          help='The weight of the package in Kg, not including '
                               'the product itself')
    volume = fields.Float('Volume',
                          digits=dp.get_precision('Stock Volume'),
                          compute='_compute_volume',
                          help='The volume of the package in m3')
    length = fields.Float('Length',
                          digits=dp.get_precision('Stock Dimension'),
                          help='The length of the package in cm')
    width = fields.Float('Width', digits=dp.get_precision('Stock Dimension'),
                         help='The width of the package in cm')
    height = fields.Float('Height',
                          digits=dp.get_precision('Stock Dimension'),
                          help='The height of the package in cm')

    # Imperial measures
    show_imperial = fields.Boolean('Show Imperial Measures',
                                   compute='_compute_show_imperial')
    volume_gal = fields.Float('Volume (Gal)',
                              digits=dp.get_precision('Stock Volume Gallon'),
                              readonly=True,
                              help='The Volume of the package in imperial '
                                   'Gallons')
    weight_lb = fields.Float('Weight (Lb)',
                             digits=dp.get_precision('Stock Weight Pound'),
                             readonly=True,
                             help='The weight of the package in pounds')
    weight_oz = fields.Float('Weight (Oz)',
                             digits=dp.get_precision('Stock Weight Ounce'),
                             readonly=True,
                             help='The weight of the package in ounces')
    length_in = fields.Float('Length (In)',
                             digits=dp.get_precision('Stock Dimension'),
                             compute='update_dimension_imp',
                             help='The length of the package in inch')
    width_in = fields.Float('Width (In)',
                            digits=dp.get_precision('Stock Dimension'),
                            compute='update_dimension_imp',
                            help='The width of the package in inch')
    height_in = fields.Float('Height (In)',
                             digits=dp.get_precision('Stock Dimension'),
                             compute='update_dimension_imp',
                             help='The height of the package in inch')

    @api.multi
    def _compute_show_imperial(self):
        show_imp = self.env.user.company_id.show_imperial_measures
        for package in self:
            package.show_imperial = show_imp

    @api.multi
    @api.onchange('weight')
    @api.constrains('weight')
    def update_weight_imp(self):
        """
        Compute imperial units on changing weight
        """
        for package in self:
            oz = package.weight * 35.27396195
            package.weight_lb = int(oz / 16)
            package.weight_oz = oz % 16

    @api.multi
    @api.onchange('length', 'width', 'height')
    @api.depends('length', 'width', 'height')
    def update_dimension_imp(self):
        """
        Compute imperial units on changing dimensions
        """
        for package in self:
            package.length_in = package.length * 0.3937007874
            package.width_in = package.width * 0.3937007874
            package.height_in = package.height * 0.3937007874

    @api.multi
    @api.depends('length', 'width', 'height')
    @api.onchange('length', 'width', 'height')
    @api.constrains('length', 'width', 'height')
    def _compute_volume(self):
        """
        Compute volume
        """
        for package in self:
            if package.length and package.width and package.height:
                # get volume in m3
                volume = (package.length / 100.0) * (
                        package.width / 100.0) * (package.height / 100.0)
                package.volume = volume
                package.volume_gal = volume * 219.96924829909
