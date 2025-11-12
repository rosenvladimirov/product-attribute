#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductPropertiesPrintMixin(models.AbstractModel):
    _name = 'product.properties.print.mixin'
    _description = "Product properties print Mixin"

    use_product_properties = fields.Selection([
        ('description', 'Use descriptions'),
        ('properties', 'Use properties'),
    ],
        string="Type product description",
        help='Choice type of the view for product description',
        default="description"
    )
    category_print_properties = fields.Many2one('product.properties.print.category',
                                                'Default Print properties category')
    products_properties_env_ref = fields.Char('Product properties env.ref')
    products_properties = fields.Html('Products properties', compute="_get_products_properties")
    invoice_sub_type = fields.Many2one("product.properties.static.dropdown",
                                       compute="_compute_invoice_sub_type",
                                       inverse="_inverse_invoice_sub_type",
                                       )

    def _compute_invoice_sub_type(self):
        for record in self:
            if record.print_properties:
                invoice_sub_type = record.print_properties.filtered(lambda r: r.invoice_sub_type)
                if invoice_sub_type:
                    record.invoice_sub_type = invoice_sub_type.invoice_sub_type
                else:
                    record.invoice_sub_type = False
            else:
                record.invoice_sub_type = False

    def _inverse_invoice_sub_type(self):
        for record in self:
            if record.invoice_sub_type:
                invoice_sub_type = record.print_properties.filtered(lambda r: r.invoice_sub_type)
                if invoice_sub_type:
                    invoice_sub_type.invoice_sub_type = record.invoice_sub_type
                else:
                    record.print_properties = [Command.create({
                        'invoice_sub_type': record.invoice_sub_type.id,
                        'print': True,
                        'sequence': 9999,
                    })]
            else:
                record.print_properties.filtered(lambda r: r.invoice_sub_type).unlink()

    @api.depends('products_properties_env_ref')
    def _get_products_properties(self):
        for record in self:
            record.products_properties = record._get_html(record.products_properties_env_ref)

    def _get_html(self, ref=False):
        if not ref:
            return False
        try:
            view = self.env.ref(ref)
            render_context = {
                'o': self,
            }
            return view._render_template(view.id, render_context)
        except ValidationError as e:
            _logger.info(f"Error when rendering products properties.\n{e}")
            return False

    def toggle_use_product_properties(self):
        for record in self:
            use_product_properties = {'description': 'properties', 'properties': 'description'}
            record.use_product_properties = use_product_properties[record.use_product_properties]
            # _logger.info(f"{record.use_product_properties}")

    def remove_all_print_properties(self):
        for record in self:
            record.print_properties = False

    def set_products_print_properties(self, record, lines=False):
        record.print_properties = self.env['product.properties'].\
            set_products_print_properties(record, getattr(record, lines))

    def set_all_print_properties(self, record, lines=False, mode=None):
        if not lines:
            lines = 'order_line'
        record.print_properties = self.env['product.properties'].set_all_print_properties(record,
                                                                                          getattr(record, lines),
                                                                                          mode=mode)

    def _get_target_field(self, target_field_name=False):
        if not target_field_name:
            if self._name == 'sale.order':
                target_field_name = 'sale_id'
            elif self._name == 'stock.picking':
                target_field_name = 'picking_id'
            elif self._name == 'account.move':
                target_field_name = 'invoice_id'
            elif self._name == 'res.partner':
                target_field_name = 'partner_id'
            elif self._name == 'purchase.order':
                target_field_name = 'purchase_id'
        return target_field_name

    def _values_partner_print_properties(self, record, target_field_name):
        return {
                'name': record.name.id,
                'print': True,
                target_field_name: self.id,
                'sequence': record.sequence,
            }

    def set_partner_print_properties(self, record_from=False, record_to=False, target_field_name=False):
        if not record_to and not record_from:
            return
        if record_to and not record_from:
            record_from = record_to.parent_id
        if not target_field_name:
            target_field_name = record_to._get_target_field(target_field_name)

        print_properties = []
        source = record_from.parent_id and record_from.parent_id or record_from
        partner_print_ids = [x for x in source.print_properties.filtered(lambda x: x.name and not x.static_field)]
        partner_static_print_ids = [x for x in source.print_properties.filtered(lambda x: x.print and x.static_field)]
        if source.print_properties and not record_to.print_properties:
            print_properties += [Command.create(
                self._values_partner_print_properties(x, target_field_name)
            ) for x in partner_print_ids]
            if partner_static_print_ids:
                print_properties += [Command.create({
                    'static_field': x.static_field,
                    'print': True,
                    target_field_name: self.id,
                    'sequence': 9999,
                }) for x in partner_static_print_ids]
            # _logger.info(f"Partner Print {print_properties}")
            record_to.print_properties = print_properties

    def get_static_field(self, field_name):
        res = False
        for record in self:
            product_properties_print = record.print_properties.filtered(lambda p: p.static_field == field_name)
            if product_properties_print:
                if len(product_properties_print) > 1:
                    product_properties_print = product_properties_print[0]
                res = product_properties_print.print
        return res

    def set_static_field(self, field_name, force_print=True, target_field_name=False):
        for record in self:
            target_field_name = record._get_target_field(target_field_name=target_field_name)
            product_properties_print = record.print_properties.filtered(lambda p: p.static_field == field_name)
            # _logger.info(f"SET STATIC PROPERTIES {record._name}:{target_field_name}:{force_print}:{field_name}:{product_properties_print}")
            if target_field_name:
                if force_print and not product_properties_print:
                    record.print_properties |= self.env['product.properties.print'].new({
                        target_field_name: record.id,
                        'static_field': field_name,
                        'print': force_print,
                        'sequence': 9999,
                    })
                if not force_print and product_properties_print:
                    record.print_properties = record.print_properties - product_properties_print
                # _logger.info(f"{record.print_properties} changed patient visit")
