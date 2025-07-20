#  Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import UserError


class ProductPropertiesPrintCategory(models.Model):
    _name = "product.properties.print.category"
    _description = "Category Product properties for default printing"

    name = fields.Char('Property name', required=True, translate=True)
    type_ids = fields.One2many("product.properties.print.line.category", inverse_name="print_id",
                               string="Type Property")
    type_static_id = fields.Many2one("product.properties.static", 'Static Product properties')


class ProductPropertiesPrintLineCategory(models.Model):
    _name = "product.properties.print.line.category"
    _description = "Category lines Product properties for default printing"

    print_id = fields.Many2one('product.properties.print.category', 'Property name', required=True, index=True)
    sequence = fields.Integer("Sequence",
                              related='type_id.sequence',
                              index=True,
                              store=True,
                              help="The first in the sequence is the default one.")
    type_id = fields.Many2one("product.properties.type", string="Type Property")
    name = fields.Char('Name', related='type_id.name', store=True)
    static_field = fields.Selection(
        selection=lambda self: self.env['product.properties.static']._get_field_name_filter(),
        string="Static Properties Field name")
    display_name = fields.Char(compute='_compute_display_name')
    invoice_sub_type = fields.Many2one("product.properties.static.dropdown", string="Category Type Documents",
                                       domain="[('field_name', '=', 'invoice_sub_type')]")

    @api.depends('type_id', 'print_id')
    def _compute_display_name(self):
        for type in self:
            if type.type_id:
                type.display_name = "[%s] %s" % (type.sequence, type.name)
            else:
                type.display_name = "%s" % type.static_field

    @api.depends('sequence')
    @api.onchange('type_id')
    def onchange_type_id(self):
        for record in self:
            if record.type_id:
                record.sequence = record.type_id.sequence
                record.name = record.type_id.name
