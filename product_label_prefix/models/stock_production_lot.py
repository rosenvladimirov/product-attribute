# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    description_short = fields.Char("Short description", compute="_get_description_short")

    @api.depends('product_id')
    def _get_description_short(self):
        for line in self:
            line.description_short = line.product_id and line.product_id.description_short and line.product_id.description_short or line.product_id.product_tmpl_id.description_short

    @api.onchange('ref')
    def on_change_ref(self):
        if self.product_id.product_tmpl_id.label_separator and self.ref[-1] != self.product_id.product_tmpl_id.label_separator:
            self.ref = '%s%s' % (self.ref, self.product_id.product_tmpl_id.label_separator)

    def action_lots_ref_glabel_print(self):
        self.ensure_one()
        ctx = self._context.copy()
        ctx['active_model'] = 'stock.production.lot'
        ctx['active_id'] = self.id
        return self.env['ir.actions.report']._get_report_from_name('lot_ref_label').with_context(ctx).report_action(self)
