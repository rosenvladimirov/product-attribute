#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, tools, _, Command
from .product_properties import MAGIC_FIELDS

_logger = logging.getLogger(__name__)


class ProductPropertiesStatic(models.Model):
    _name = "product.properties.static"
    _description = "Product static properties"
    _order = "sequence, id"

    def _get_field_name_filter(self):
        res = [('invoice_sub_type', _('Document sub types'))]
        for g in filter(lambda r: r not in self.ignore_fields(), self._fields):
            field = self.fields_get(g)[g]
            res.append((g, field['string']))
        return res

    @api.model
    def ignore_fields(self):
        return MAGIC_FIELDS + ['sequence', 'company_id', 'name', 'object_id', 'currency_id']

    @api.model
    def static_property_fields(self):
        return list(filter(lambda r: r not in self.ignore_fields(), self._fields))

    # to check where is lost
    def _link_domain(self):
        return [('model', 'in', ['product.product', 'product.template'])]

    def _links_get(self):
        return [(r.model, r.name) for r in self.env['ir.model.fields'].search(self._link_domain())]

    name = fields.Char('Name', required=True)
    sequence = fields.Integer("Sequence", default=9999, index=True,
                              help="The first in the sequence is the default one.")
    object_id = fields.Reference(string='Reference', selection=_links_get, readonly=True, ondelete="set null")
    currency_id = fields.Many2one('res.currency', string='Currency of properties',
                                  default=lambda self: self.env.user.company_id.currency_id)
    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('object_id', 'name')
    def _compute_display_name(self):
        for record in self:
            if record.object_id:
                record.display_name = "%s: %s" % (record.name, record.object_id.name_get()[0][1])
            else:
                record.display_name = "[%s] %s" % (record.sequence, record.name)

    @api.depends('name', 'object_id')
    def name_get(self):
        result = []
        for static_properties in self:
            name = static_properties.name
            if static_properties.object_id:
                name = "[%s] %s" % (static_properties.sequence, static_properties.object_id.name_get()[0][1])
            result.append((static_properties.id, name))
        return result

    def _display_type(self):
        if self._context.get('block'):
            return False

    def _set_static_ignore_print_properties(self):
        return ['invoice_sub_type']

    def default_get(self, fields_list):
        res = super(ProductPropertiesStatic, self).default_get(fields_list)
        res.update({
            'sequence': 9999,
            'name': '9999',
        })
        return res

    @api.model
    def static_property_data(self, res, vals, updates=None, product_variant_id=False):
        if 'product_prop_static_id' not in res._fields:
            return vals

        static_properties_obj = self.env['product.properties.static']
        static_ids = self.static_property_fields()
        v_static_ids = list(map(lambda x: 'v' + x, static_ids))
        property_data = static_properties_obj.default_get(static_ids)

        if res:
            property_data.update({'object_id': "%s,%d" % ("%s" % res._name, res.id)})

        if not product_variant_id \
            and res._name == 'product.template' \
            and res.product_variant_count == 1:
            product_variant_id = res.product_variant_id

        if res._name in ('product.product', 'product.template') and product_variant_id:
            res = product_variant_id

        if any([x in vals for x in static_ids]):
            if not property_data:
                property_data = {}
            for field in static_ids:
                if res and field in res._fields:
                    field_value = vals.get(field) and vals[field] or getattr(res, field)
                    field_name = static_properties_obj.fields_get(field)[field]
                    if not vals.get(field, False) and field_name['type'] == 'many2one':
                        field_value = field_value.id
                    property_data.update({field: field_value})
        if any([x in vals for x in v_static_ids]):
            if not property_data:
                property_data = {}
            for field in static_ids:
                if res and 'v' + field in res._fields:
                    field_value = vals.get('v' + field) and vals['v' + field] or getattr(res, 'v' + field)
                    if static_properties_obj.fields_get('v' + field).get('v' + field):
                        field_name = static_properties_obj.fields_get('v' + field)['v' + field]
                        if not vals.get(field, False) and field_name['type'] == 'many2one':
                            field_value = field_value.id
                        property_data.update({field: field_value})
            for field in v_static_ids:
                if vals.get(field):
                    del vals[field]
        # _logger.info("PROPERTIES %s" % property_data)
        if property_data:
            vals.update({'product_prop_static_id': property_data})
        for field in static_ids:
            if vals.get(field):
                del vals[field]
        if updates is not None:
            vals.update(updates)
        return vals

    @api.model
    def update_static_property_data(self, vals):
        values = {}
        static_ids = self.env['product.properties.static'].static_property_fields()
        for key in vals.keys():
            for static_field in static_ids:
                if key == static_field or key == f'v{static_field}':
                    values[static_field] = vals[key]
                    break
            #
            # if any([x in vals for x in static_ids]):
            #     for x in static_ids:
            #         if vals.get(x) or vals.get(f'v{x}'):
            #             if vals.get(f'v{x}'):
            #                 values[x] = vals.get(f'v{x}')
            #             else:
            #                 values[x] = vals[x]
        _logger.info(f"update_static_property_data values: {values}-{static_ids}")
        return values


class ProductPropertiesStaticDropdown(models.Model):
    _name = "product.properties.static.dropdown"
    _description = "The properties static dropdown"
    _order = "name, sequence, code"

    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    name = fields.Char('Name', required=True, index=True, translate=True)
    code = fields.Char('code')
    field_name = fields.Selection(
        selection=lambda self: self.env['product.properties.static']._get_field_name_filter(),
        string="Static Properties Field name")
    color = fields.Integer(string='Color Index')

    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for dropdown in self:
            if dropdown.code:
                name = "[%s] %s" % (dropdown.code, dropdown.name)
            else:
                name = dropdown.name
            result.append((dropdown.id, name))
        return result
