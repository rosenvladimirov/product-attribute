# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductBrand(models.Model):
    _inherit = 'product.brand'

    manufacturer = fields.Many2one('product.manufacturer', string="Product Manufacturer")

    @api.multi
    def action_see_datasheets(self):
        domain = [
            '&', ('res_model', '=', 'product.brand'), ('res_id', '=', self.id)
        ]
        attachment_view = self.env.ref('product_properties.view_product_manufacturer_datasheets_eazy_kanban')
        return {
            'name': _('Datasheets'),
            'domain': domain,
            'res_model': 'product.manufacturer.datasheets',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                        Click to upload datasheet to your product.
                    </p><p>
                        Use this feature to store any files, like drawings or specifications.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % ('product.brand', self.id)
            }
