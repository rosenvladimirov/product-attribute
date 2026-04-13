# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

# Moisture sensitivity levels
MOISTURE_LEVELS = [
    ('1', 'MSL 1 - Unlimited'),
    ('2', 'MSL 2 - 1 year'),
    ('2a', 'MSL 2a - 4 weeks'),
    ('3', 'MSL 3 - 168 hours'),
    ('4', 'MSL 4 - 72 hours'),
    ('5', 'MSL 5 - 24 hours'),
    ('5a', 'MSL 5a - 24 hours'),
    ('6', 'MSL 6 - Mandatory bake'),
]
# Storage conditions selection options
STORAGE_CONDITIONS = [
    ('normal', '15-30°C, 45-75% RH'),
    ('dry', '<5% RH'),
    ('cold', '2-8°C'),
]
DAYS_IN_MONTH = 30
HOURS_IN_DAY = 24
SECONDS_IN_HOUR = 3600


class ProductTemplate(models.Model):
    _inherit = "product.template"

    component_type_id = fields.Many2one(
        'component.definition.properties',
        compute='_compute_component_type_id',
        inverse='_inverse_component_type_id',
        search="_search_component_type_id",
        string='Component Type',
        store=True,
    )

    component_properties = fields.Properties(
        'Component technical data',
        compute='_compute_component_properties',
        inverse='_inverse_component_properties',
        definition='component_type_id.component_properties_definition',
        store=True,
        precompute=False,
    )
    moisture_sensitivity_level = fields.Selection(
        MOISTURE_LEVELS,
        compute='_compute_moisture_sensitivity_level',
        inverse='_inverse_moisture_sensitivity_level',
        search="_search_moisture_sensitivity_level",
        string='MSL',
        store=True,
    )

    esd_protection = fields.Boolean(
        string='ESD Protection',
        help='Indicates if the packaging has ESD protection'
    )

    storage_conditions = fields.Selection(
        STORAGE_CONDITIONS,
        string='Storage Conditions'
    )

    shelf_life = fields.Integer(
        string='Shelf Life (months)',
        help='Shelf life in months under specified storage conditions'
    )

    @api.depends('manufacturer_ids')
    def _compute_manufacturer_id(self):
        for record in self:
            if len(record.manufacturer_ids) > 0:
                record.manufacturer_id = record.manufacturer_ids[0]
            else:
                record.manufacturer_id = False

    @api.depends('product_variant_ids', 'product_variant_ids.component_type_id')
    def _compute_component_type_id(self):
        for record in self:
            if record.product_variant_count == 1:
                record.component_type_id = record.product_variant_ids[0].component_type_id
            else:
                record.component_type_id = False

    def _inverse_component_type_id(self):
        for record in self:
            for product_id in record.product_variant_ids:
                if product_id.component_type_id != record.component_type_id:
                    product_id.write({'component_properties': False})
                product_id.component_type_id = record.component_type_id

    def _search_component_type_id(self, operator, value):
        ids = self.env['product.product'].search([('component_type_id', operator, value)]).mapped('product_tmpl_id').ids
        return [('id', 'in', ids)]

    @api.depends('product_variant_ids.component_properties')
    def _compute_component_properties(self):
        for record in self:
            if record.product_variant_id:
                record.component_properties = record.product_variant_id.component_properties

    def _inverse_component_properties(self):
        for record in self:
            if record.product_variant_count == 1 and record.component_properties:
                for product_id in record.product_variant_ids.\
                    filtered(lambda p: p.component_properties != record.component_properties):
                    product_id.write({'component_properties': record.component_properties})

    def _search_component_properties(self, operator, value):
        ids = self.env['product.product'].search([('component_properties', operator, value)]).mapped('product_tmpl_id').ids
        return [('id', 'in', ids)]

    @api.depends('product_variant_ids', 'product_variant_ids.moisture_sensitivity_level')
    def _compute_moisture_sensitivity_level(self):
        for record in self:
            if record.product_variant_count == 1:
                record.moisture_sensitivity_level = record.product_variant_ids[0].moisture_sensitivity_level
            else:
                record.moisture_sensitivity_level = False

    def _inverse_moisture_sensitivity_level(self):
        for record in self:
            if record.product_variant_count == 1 and record.moisture_sensitivity_level:
                for product_id in record.product_variant_ids.\
                    filtered(lambda p: p.moisture_sensitivity_level != record.moisture_sensitivity_level):
                    product_id.write({'moisture_sensitivity_level': record.moisture_sensitivity_level})

    def _search_moisture_sensitivity_level(self, operator, value):
        ids = self.env['product.product'].search([('moisture_sensitivity_level', operator, value)]).mapped('product_tmpl_id').ids
        return [('id', 'in', ids)]

    def action_update_nexar_data(self):
        for record in self:
            for product_id in record.product_variant_ids:
                product_id.action_update_nexar_data()

    @staticmethod
    def _calculate_expiration_time(shelf_life_months):
        """
        Calculates the expiration time in seconds based on the given shelf life in the past months.

        This method computes the expiration duration starting from the current date
        for the provided shelf life period (in months). The calculation first determines
        the expiration date by adding the specified number of months to the current date.
        Subsequently, the remaining time is converted into total seconds, including both
        days and additional seconds.

        This functionality is primarily useful in scenarios where precise expiration details
        need to be determined, such as inventory management or time-sensitive data management.

        :param shelf_life_months: Number of months for the shelf life duration.
        :type shelf_life_months: int
        :return: Expiration duration in seconds from the current date.
        :rtype: int
        """
        today_date = fields.Date.today()
        expiration_date = today_date + relativedelta(months=shelf_life_months)
        time_delta = expiration_date - today_date
        return time_delta.days

    def _set_expiration_fields(self, vals, shelf_life_months):
        """
        Sets the expiration-related fields in the provided dictionary of values
        based on the given shelf life in months. It calculates the expiration
        time and marks the values to use the expiration date.

        :param vals: A dictionary to be updated with expiration fields.
        :type vals: dict
        :param shelf_life_months: The shelf life of the product in months.
        :type shelf_life_months: int
        :return: None
        """
        vals['expiration_time'] = self._calculate_expiration_time(shelf_life_months)
        vals['use_expiration_date'] = True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('shelf_life'):
                self._set_expiration_fields(vals, vals['shelf_life'])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('shelf_life'):
            self._set_expiration_fields(vals, vals['shelf_life'])
        return super().write(vals)

