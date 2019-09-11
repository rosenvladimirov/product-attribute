# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class AccountTax(models.Model):
    _inherit = 'account.tax'

    amount_type = fields.Selection(seletction_add=[
                                    ('taric', 'Customs rate base on TARIC'),
                                    ('percent_taric', 'Percentage of Price base on TARIC')
                                    #('fixed_taric_base_on_weight', 'Fixed base on weight')
                                    ])
    hs_code_id = fields.Many2one(
        comodel_name='hs.code',
        string='TARIC Code', ondelete='restrict')
    weight = fields.Float(string='Weight from TARIC', digits=dp.get_precision('Stock Weight'))

    @api.depends('name', 'hs_code_id')
    def name_get(self):
        result = []
        for account_tax in self:
            name = "%s" % ("[%s] " % account_tax.hs_code_id and account_tax.hs_code_id.taric_code or "" + account_tax.name)
            result.append((account_tax.id, name))
        return result

    @api.onchange('amount_type')
    def onchange_amount_type(self):
        if self.amount_type not in ('group', 'taric'):
            self.children_tax_ids = [(5,)]

class AccountInvoiceVATType(models.Model):
    _inherit = "account.vattype"

    applicability = fields.Selection(selection_add=[
                    ('customs', 'Used in customs declarations'),
                    ])
