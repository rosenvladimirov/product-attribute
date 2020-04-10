# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, SUPERUSER_ID, _

import logging
_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.one
    def _count_manufacture(self):
        return len([x.id for x in self.manufacture_ids])

    @api.one
    def _check_distributor_id(self):
        return len([x.id for x in self.manufacture_ids]) > 0

    manufacture_ids = fields.One2many('product.manufacturer', 'distributor_id', string='Manufacture Company', domain=[('active', '=', True)])
    count_manufacture = fields.Integer("Distributors", compute=_count_manufacture)
    distributor = fields.Boolean(compute=_check_distributor_id, string="Is Distributor")

