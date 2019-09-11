# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)



class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    customs_agent_id = fields.Many2one('res.users', string='Customs agent',
                                   help='The internal user that is in charge of communicating with Customs agence if any.')

    @api.model
    def _get_refund_copy_fields(self):
        return super(AccountInvoice, self)._get_refund_copy_fields() + ['customs_agent_id']


class AccountInvoice(models.Model):
    _inherit = "account.invoice.line"

    taric_code = fields.Char("Taric code", compute="_get_taric_code")
    hs_code_id = fields.Many2one(
        comodel_name='hs.code',
        string='Taric Code', ondelete='restrict')

    @api.depends('product_id')
    def _get_taric_code(self):
        for record in self:
            if record.product_id.type == 'service':
                record.taric_code = False
            else:
                if record.product_id.hs_code_id:
                    record.taric_code = record.product_id.hs_code_id.taric_code
                elif record.product_id.hs_code_categ_id:
                    record.taric_code = record.product_id.hs_code_categ_id.taric_code
                else:
                    record.taric_code = False
            if record.product_id.type == 'service':
                record.taric_code = False

    @api.depends('product_id')
    def _get_taric_code(self):
        for record in self:
            if record.product_id.type == 'service':
                record.taric_code = False
            else:
                if record.product_id.hs_code_id:
                    record.taric_code = record.product_id.hs_code_id.taric_code
                elif record.product_id.hs_code_categ_id:
                    record.taric_code = record.product_id.hs_code_categ_id.taric_code
                else:
                    record.taric_code = False

    def _set_taxes_extend(self, taxes):
        if any(tax for tax in taxes if tax.amount_type == 'taric'):
            new_taxes = {}
            base = 0
            for item, tax in enumerate(taxes):
                if tax.amount_type == 'taric':
                    for new_tax in tax.children_tax_ids:
                        if new_tax.amount_type in ('percent_taric', 'fixed_taric_base_on_weight') and self.hs_code_id.id == new_tax.hs_code_id.id:
                            if new_tax.amount_type == 'fixed_taric_base_on_weight':
                                new_tax['amount'] = new_tax['amount']*(self.weight/new_tax.weight)
                            new_taxes[item].append(new_tax)

            for key, val in new_taxes.items():
                del taxes[key+base]
                base = base -1
                for tax in val:
                    taxes.insert(key, tax)
                    base = base + 1
        return taxes
