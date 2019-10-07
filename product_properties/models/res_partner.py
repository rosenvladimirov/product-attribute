# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    count_datasheets = fields.Integer('Count Datasheets', compute='_compute_has_datasheets')
    print_properties = fields.One2many('product.properties.print', 'partner_id', 'Print poperties')
    product_manufacture_ids = fields.One2many('product.manufacturer', 'manufacturer', string='Products')
    is_manufacturier = fields.Boolean('Manufacturer', compute='_compute_is_manufacturier')
    #manufacture_ids = fields.Many2many('res.partner', '_compute_manufacture_ids')

    distributor_ids = fields.Many2many('product.supplierinfo', compute='_compute_distributor_ids')
    has_distributor = fields.Boolean('Manufacturer', compute='_compute_has_distributor')

    authorised_id = fields.Many2one('res.partner', 'Authorised Representative')
    qc_manager_id = fields.Many2one('res.partner', 'Quality Manager')
    req_manager_id = fields.Many2one('res.partner', 'Regulatory Manager')
    compl_manager_id = fields.Many2one('res.partner', 'Compliance Manager')
    #notified_body_ids = fields.Many2many('res.partner', string='Sertificates Notified Body')
    product_brand_ids = fields.One2many('product.brand', 'partner_id', string='Product brands')

    def __init__(self, pool, cr):
        cr.execute("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'res_partner' AND column_name = 'authorised_id'")
        if not cr.fetchone():
            cr.execute('ALTER TABLE res_partner '
                       'ADD COLUMN authorised_id integer;')

        cr.execute("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'res_partner' AND column_name = 'qc_manager_id'")
        if not cr.fetchone():
            cr.execute('ALTER TABLE res_partner '
                       'ADD COLUMN qc_manager_id integer;')

        cr.execute("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'res_partner' AND column_name = 'req_manager_id'")
        if not cr.fetchone():
            cr.execute('ALTER TABLE res_partner '
                       'ADD COLUMN req_manager_id integer;')

        cr.execute("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'res_partner' AND column_name = 'compl_manager_id'")
        if not cr.fetchone():
            cr.execute('ALTER TABLE res_partner '
                       'ADD COLUMN compl_manager_id integer;')
        return super(ResPartner, self).__init__(pool, cr)

    @api.one
    @api.depends('product_manufacture_ids')
    def _compute_is_manufacturier(self):
        self.is_manufacturier = len(self.product_manufacture_ids.ids) > 0

    @api.one
    @api.depends('distributor_ids')
    def _compute_has_distributor(self):
        self.is_manufacturier = len(self.distributor_ids.ids) > 0

    @api.multi
    def _compute_distributor_ids(self):
        for partner in self:
            if partner.product_manufacture_ids:
                distributor_ids = []
                for x in partner.product_manufacture_ids:
                    distributor_ids += [s.id for s in x.supplierinfo_ids]
                if distributor_ids:
                    partner.distributor_ids = [(6, False, distributor_ids)]
                else:
                    partner.distributor_ids = False
            else:
                partner.distributor_ids = False

    @api.one
    def _compute_has_datasheets(self):
        #'&', ('res_model', '=', 'product.brand'), ('res_id', 'in', self.product_brand_ids.ids)
        domain = ["|","|",
            '&', ('res_model', '=', 'res.partner'), ('res_id', '=', self.id),
            ('manufacturer_id', 'in', self.product_manufacture_ids.ids),
            '&', ('res_model', '=', 'product.brand'), ('res_id', 'in', self.product_brand_ids.ids)
            ]
        nbr_datasheet = self.env['product.manufacturer.datasheets'].search_count(domain)
        self.count_datasheets = nbr_datasheet

    @api.multi
    def action_see_datasheets(self):
        #'&', ('res_model', '=', 'product.brand'), ('res_id', 'in', self.product_brand_ids.ids)
        domain = ["|","|",
            '&', ('res_model', '=', 'res.partner'), ('res_id', '=', self.id),
            ('manufacturer_id', 'in', self.product_manufacture_ids.ids),
            '&', ('res_model', '=', 'product.brand'), ('res_id', 'in', self.product_brand_ids.ids)
            ]

        attchment_view = self.env.ref('product_properties.view_product_manufacturer_datasheets_eazy_kanban')
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
            'context': "{'default_res_model': '%s','default_res_id': %d, 'partner_id': %d}" % ('res.partner', self.id, self.id)
            }
