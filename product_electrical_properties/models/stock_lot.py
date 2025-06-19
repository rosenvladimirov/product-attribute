# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from odoo import models, _, api, fields


class StockLot(models.Model):
    _inherit = 'stock.lot'

    data_code = fields.Char(string='Data Code')
    mbb_mounts = fields.Integer(related='product_id.shelf_life', string='Mounts', readonly=True)
    mbb_status = fields.Selection([
        ('sealed', 'Sealed'),
        ('opened', 'Open'),
        ('baked', 'Baked')
    ], string='MBB status', default='sealed')
    mbb_opening_date = fields.Datetime('MBB opening date')
    moisture_sensitivity_level = fields.Selection(
        related='product_id.moisture_sensitivity_level',
    )
    msl_expiry_date = fields.Datetime('MSL deadline', compute='_compute_msl_expiry')
    mbb_color = fields.Integer(string='Color', compute='_compute_mbb_color', store=True)

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get('product_id') and not res.get('mbb_mounts'):
            product = self.env['product.product'].browse(res['product_id'])
            res['mbb_mounts'] = product.product_tmpl_id.shelf_life
        return res

    @api.depends('mbb_status')
    def _compute_mbb_color(self):
        for record in self:
            if record.mbb_status == 'sealed':
                record.mbb_color = 8
            elif record.mbb_status == 'opened':
                record.mbb_color = 3
            elif record.mbb_status == 'baked':
                record.mbb_color = 1  # червено
            else:
                record.mbb_color = 0  # сиво

    @api.depends('mbb_opening_date', 'moisture_sensitivity_level')
    def _compute_msl_expiry(self):
        for record in self:
            if record.mbb_opening_date and record.moisture_sensitivity_level:
                hours = {
                    '1': False,  # неограничено
                    '2': 8760,   # 1 година
                    '2a': 672,   # 4 седмици
                    '3': 168,    # 168 часа
                    '4': 72,     # 72 часа
                    '5': 24,     # 24 часа
                    '5a': 24,    # 24 часа
                    '6': 0       # изисква изпичане
                }
                if record.moisture_sensitivity_level in hours and hours[record.moisture_sensitivity_level]:
                    record.msl_expiry_date = record.mbb_opening_date + timedelta(hours=hours[record.moisture_sensitivity_level])
                    record.expiry_date = record.msl_expiry_date
                else:
                    record.msl_expiry_date = False


    def _process_data_code(self, vals, product=None):
        """
        Processes the data code provided in the given values dictionary to compute and set
        the creation date, expiration date, and related flags if applicable. This method
        is used to ensure that product-specific expiration handling is applied
        based on the provided or defaulted product.

        :param vals: A dictionary containing the data to process. Expected to include
                     the 'data_code' key, which is a string in the format "%y%W".
        :param product: Optional product instance. If not provided, it is derived using
                        the 'product_id' key in vals. Defaults to None.
        :return: None
        """
        if not vals.get('data_code'):
            return

        parsed_date = datetime.strptime(vals['data_code'], "%y%W")
        vals['create_date'] = parsed_date

        if product is None:
            product = self.env['product.product'].browse(vals['product_id'])

        if self._should_set_expiration(product):
            vals['use_expiration_date'] = True
            vals['expiration_date'] = self._calculate_expiration_date(
                parsed_date, product.product_tmpl_id.expiration_time
            )

    @staticmethod
    def _should_set_expiration(product):
        """
        Determines whether the expiration should be set for a given product. This
        method checks various conditions related to the product, including its
        template and attributes.

        :param product: The product instance to check.
        :type product: Any
        :return: True if expiration should be set, otherwise False.
        :rtype: bool
        """
        return (product and
                product.product_tmpl_id and
                product.product_tmpl_id.expiration_time and
                product.moisture_sensitivity_level != '1')

    def _calculate_expiration_date(self, base_date, expiration_days):
        """
        Calculate the expiration date by adding a specified number of days
        to a given base date.

        :param base_date: The starting date to calculate from.
        :param expiration_days: The number of days to add to the base date to determine
            the expiration date.
        :return: The calculated expiration date.
        """
        return base_date + timedelta(days=expiration_days)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._process_data_code(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._process_data_code(vals, self.product_id)
        return super().write(vals)
