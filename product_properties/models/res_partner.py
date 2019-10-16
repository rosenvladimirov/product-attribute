# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    count_datasheets = fields.Integer('Count Datasheets', compute='_compute_has_datasheets')
    print_properties = fields.One2many('product.properties.print', 'partner_id', 'Print poperties')

    @api.one
    def _compute_has_datasheets(self):
        domain = ['|',
            '&', ('res_model', '=', 'res.partner'), ('res_id', '=', self.id),
            "|", ('manufacturer_id', '=', False), ('manufacturer_id', '=', self.id)]
        nbr_datasheet = self.env['product.manufacturer.datasheets'].search_count(domain)
        self.count_datasheets = nbr_datasheet

    @api.multi
    def action_see_datasheets(self):
        domain = ['|',
            '&', ('res_model', '=', 'res.partner'), ('res_id', '=', self.id),
            "|", ('manufacturer_id', '=', False), ('manufacturer_id', '=', self.id)]

        attchment_view = self.env.ref('product_properties.view_datasheets_file_kanban_properties')
        return {
            'name': _('Datasheets'),
            'domain': domain,
            'res_model': 'product.manufacturer.datasheets',
            'type': 'ir.actions.act_window',
            'view_id': attchment_view.id,
            'views': [(attchment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                        Click to upload datasheet to your product.
                    </p><p>
                        Use this feature to store any files, like drawings or specifications.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % ('res.partner', self.id)
            }
