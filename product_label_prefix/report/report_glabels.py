# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, tools, _

import logging
_logger = logging.getLogger(__name__)


class ReportGlabelsAbstract(models.AbstractModel):
    _inherit = 'report.report_glabels.abstract'

    @api.model
    def records_glabels_report(self, ids, data):
        ctx = self._context.copy()
        model = ctx['active_model']
        if model == "stock.production.lot":
            records = []
            record_obj = self.env[model].browse(ids)
            for lot in record_obj:
                qty = sum(x.quantity - x.reserved_quantity for x in lot.quant_ids.filtered(lambda r: r.location_id.usage in ['internal', 'transit'] and not r.location_id.partner_id))
                records.append({'name': "".join(['label_prefix_code' in lot.product_id.product_tmpl_id._fields and lot.product_id.product_tmpl_id.label_prefix_code or '' or '', lot.name]),
                                'last_letter': lot.name and lot.name[-1] or '',
                                'display_name': "+".join([lot.name or '', lot.ref or '', str(int(qty or 0.0))]),
                                'ref': lot.ref,
                                'date': lot.create_date,
                                'product_name': lot.product_id.name,
                                'description_short': lot.description_short,
                                'product_barcode': lot.product_id.product_tmpl_id.barcode,
                                'product_default_code': lot.product_id.product_tmpl_id.default_code,
                                'product_electrical_properties_package': 'electrical_properties_package' in lot.product_id.product_tmpl_id._fields and lot.product_id.product_tmpl_id.electrical_properties_package or '',
                                'product_electrical_properties_msl': 'electrical_properties_msl' in lot.product_id.product_tmpl_id._fields and lot.product_id.product_tmpl_id.electrical_properties_msl or ''})
            if records:
                return record_obj, records
        return super(ReportGlabelsAbstract, self).records_glabels_report(ids, data)