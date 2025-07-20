#  Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import UserError


class ProductPropertiesPrint(models.Model):
    _name = "product.properties.print"
    _description = "Product properties for printing"
    _order = "system_properties, sequence"

    def _get_domain_invoice_sub_type(self):
        return [('field_name', '=', 'invoice_sub_type')]

    name = fields.Many2one("product.properties.type", string="Property name")
    print = fields.Boolean('Print')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'product.properties.print'))
    categ_id = fields.Many2one("product.properties.category", "Category", index=True)

    partner_id = fields.Many2one('res.partner', string='Partner', index=True)
    sale_id = fields.Many2one("sale.order", string="Sale order", index=True)
    invoice_id = fields.Many2one("account.move", string="Invoice", index=True)
    picking_id = fields.Many2one("stock.picking", string="Transfer Reference", index=True)
    purchase_id = fields.Many2one("purchase.order", string="Purchase", index=True)

    invoice_sub_type = fields.Many2one("product.properties.static.dropdown", string="Type Documents",
                                       domain=lambda self: self._get_domain_invoice_sub_type())

    system_properties = fields.Boolean('System used')
    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    static_field = fields.Selection(
        selection=lambda self: self.env['product.properties.static']._get_field_name_filter(),
        string="Static Properties Field name")

    def _compute_display_name(self):
        name = dict(self.env['product.properties.static']._get_field_name_filter())
        for record in self:
            display_name = []
            if record.name:
                display_name.append(record.name.name)
            elif record.static_field:
                display_name.append(name.get(record.static_field))
            elif record.invoice_sub_type:
                display_name.append(record.invoice_sub_type.name)
            record.display_name = "-".join(display_name)

    def get_print_properties(self, source=False):
        return [x.name.id for x in self if not x.static_field and x.print]

    def get_print_static_properties(self, source=False):
        return [x.static_field for x in self if x.static_field and x.print]

    def unlink(self):
        for properties in self:
            if properties.system_properties:
                raise UserError(_('You cannot delete system properties.'))
        return super(ProductPropertiesPrint, self).unlink()
