#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, tools, _, Command
from odoo.tools import pycompat, safe_eval
from .product_properties import TYPES, _clean_website

_logger = logging.getLogger(__name__)


class ProductPropertiesType(models.Model):
    _name = "product.properties.type"
    _description = "The Properties types"
    _order = "sequence, id"

    def _get_domain_type_field_model_id(self):
        return [('model', 'in', ['product.product',
                                 'product.template',
                                 'product.pricelist.item',
                                 'sale.order.line',
                                 'account.invoice.line',
                                 'purchase.order.line',
                                 'stock.move.line'])]

    name = fields.Char('Type Name', required=True, index=True, translate=True)
    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    type_fields = fields.Selection(TYPES, string="Type properties", required=True, default='char')
    type_float = fields.Float("Value for Float")
    type_char = fields.Char("Value for Char")
    type_int = fields.Integer("Value for Int")
    type_int_second = fields.Integer("Value for Second Int")
    type_eval = fields.Text("Value for Eval")
    type_currency = fields.Monetary(string="Value for Currency", currency_field="currency_id")
    type_date = fields.Date(string="Value for Date")
    type_boolean = fields.Boolean("Value for Boolean")
    type_url = fields.Char(help="URL")
    type_field = fields.Char(help="Field", compute="_get_type_field")
    type_field_model_id = fields.Many2one('ir.model', string='Target/Source Odoo model',
                                          domain=lambda self: self._get_domain_type_field_model_id())
    type_field_target = fields.Many2one('ir.model.fields', string='Target/Source Odoo field',
                                        help="Choice target/source field for collection data. "
                                             "target/source in odoo model.")
    type_package_id = fields.Many2one("product.properties.package", string="Value for Package")
    dimensions_x = fields.Float("X Dimensions")
    dimensions_y = fields.Float("Y Dimensions")
    dimensions_z = fields.Float("Z Dimensions")
    type_uom_id = fields.Many2one("product.properties.uom", string="UOM Name")
    type_dropdown_id = fields.Many2one("product.properties.dropdown", string="Dropdown")
    currency_id = fields.Many2one('res.currency', string='Currency of properties',
                                  default=lambda self: self.env.user.company_id.currency_id)

    def get_type_field_model_id(self, domain=False):
        if not domain:
            domain = self.env['product.properties.type']._get_domain_type_field_model_id()
        return domain

    def _get_type_field(self):
        for field_value in self:
            if field_value.type_field_target:
                model = self.env[field_value.type_field_target.model_id.model]
                field_value.type_field = getattr(model, field_value.type_field_target.name)
            else:
                field_value.type_field = False

    def get_product_properties_print_head(self, properties_print=False):
        static_properties_obj = self.env['product.properties.static']
        print_static_ids = []
        ret = []
        if properties_print:
            print_static_ids = properties_print.get_print_static_properties()

        if self._context.get('force_print'):
            print_static_ids = filter(lambda
                                          r: r not in static_properties_obj.ignore_fields() + static_properties_obj._set_static_ignore_print_properties(),
                                      static_properties_obj._fields)

        for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields):
            if properties_print and g in print_static_ids:
                field = static_properties_obj.fields_get(g)[g]
                ret.append({
                    'label': field['string'],
                    'field': g,
                })
        return ret

    def get_product_properties_break(self, row, br):
        return row % br

    def _get_default_currency_id(self, properties, field_name):
        return properties.currency_id

    def _get_statistic_prop(self, record):
        prop_lines = self.env['product.properties.static']
        if record._name in ['product.product', 'product.template']:
            if record.product_tmpl_id.product_prop_static_id:
                prop_lines = record.product_tmpl_id.product_prop_static_id
            if record.product_prop_static_id and record._name == 'product.product':
                prop_lines |= record.product_prop_static_id
        return prop_lines

    def get_product_properties_print(self, product, properties_print=False, line=False, lot_ids=False,
                                     codes=False, rcontext=False, prefix=False, suffix=False, force_field=False):
        ctx = rcontext and rcontext or self._context.copy()
        res = {}
        ret = []
        print_ids = []
        print_static_ids = []
        static_properties_obj = self.env['product.properties.static']

        def get_prefix(obj, prefix_field):
            # _logger.info("PUT PREFIX %s:%s" % (obj, prefix_field))
            if not prefix_field or not obj:
                return ""
            prefix_value = ""
            if len(prefix_field.split('.')) > 0:
                prefix_field_obj = prefix_field.split('.')
                # _logger.info("PREFIX SPLIT %s" % prefix_field_obj)
                try:
                    obj = getattr(obj, prefix_field_obj[0])
                    prefix_field = prefix_field_obj[1]
                except ValueError:
                    _logger.info("Cannot adapt prefix/suffix %s in object %s" % (prefix_field, obj))
                # _logger.info("PREFIX SPLIT AFTER %s:%s" % (obj, prefix_field))

            try:
                prefix_value = getattr(obj, prefix_field)
            except ValueError:
                _logger.info("Cannot adapt prefix/suffix %s in object %s" % (prefix_field, obj))

            # _logger.info("PREFIX BEFORE %s" % prefix_value)

            if prefix_value:
                prefix_value += ": "
            else:
                prefix_value = ""
            # _logger.info("PREFIX %s" % prefix_value)
            return prefix_value

        if ctx.get("lot_prefix"):
            prefix = ctx['lot_prefix']
        if ctx.get("lot_suffix"):
            suffix = ctx['lot_suffix']
        if not prefix:
            prefix = ""
        if not suffix:
            suffix = ""
        # _logger.info("RCONTEXT %s" % ctx)
        if properties_print:
            print_ids = properties_print.get_print_properties(source=product)
            print_static_ids = properties_print.get_print_static_properties(source=product)

        if self._context.get('force_print'):
            print_static_ids = filter(lambda
                                          r: r not in static_properties_obj.ignore_fields() + static_properties_obj._set_static_ignore_print_properties(),
                                      static_properties_obj._fields)

        if product._name == 'product.product' and  'product_properties_ids' in product._fields:
            properties_available = (product.product_tmpl_id.product_properties_ids, product.product_properties_ids)
        elif product._name != 'product.product' and 'product_properties_ids' in product._fields:
            properties_available = (product.product_properties_ids)
        else:
            properties_available = ()

        if line._name == 'account.move.line' and (not lot_ids or lot_ids._name == 'account.move.line'):
            lot_ids = self.env['stock.lot']
            for line_lot in line._get_invoiced_lot_values():
                if line_lot.get('lot_id'):
                    lot_ids |= self.env['stock.lot'].browse(line_lot['lot_id'])

        for properties in properties_available:
            if self._context.get('force_print'):
                print_ids = [x.name.id for x in properties]
            # else:
            #    print_ids = list(set([x.name.id for x in properties]) - set(print_ids))
            for prop_line in properties.sorted(key=lambda r: r.name.sequence):
                color = 0
                if properties_print and prop_line.name.id in print_ids:
                    _logger.info(f"Properties: {prop_line.type_field_name}-{product}-{line}-{lot_ids}")
                    currency_id = self._get_default_currency_id(prop_line, prop_line.name)
                    # if line and prop_line.type_field_name in line._fields:
                    #     prop_line.type_field_model = line._name
                    #     prop_line.model_obj_id = line.id

                    if line and prop_line.type_field_name == force_field and prop_line.type_field_name in line._fields:
                        force_field_id = getattr(line, force_field)
                        force_field_field = line.fields_get(force_field)[force_field]
                        if force_field_field['type'] == 'many2one':
                            prop_line.type_field_model = force_field_id
                            prop_line.model_obj_id = force_field_id.id

                    if lot_ids and not isinstance(lot_ids, (str,)) and prop_line.name.type_fields == 'lot':
                        res[prop_line.name.name] = {'value': '-'.join(
                            map(lambda lot_id: lot_id and get_prefix(lot_id, prefix) + lot_id.name + get_prefix(lot_id, suffix) or '', lot_ids)),
                            'field': prop_line.name.name,
                            'attrs': False, 'image': False, 'sequence': prop_line.name.sequence,
                            'type': prop_line.name.type_fields,
                            'currency_id': currency_id}
                    elif lot_ids and not isinstance(lot_ids,
                                                    (str,)) and prop_line.name.type_fields == 'use_date' and any(
                            [lot.id for lot in lot_ids if lot.lot_id and lot.lot_id.use_date]):
                        res[prop_line.name.name] = {'value': '-'.join(
                            map(lambda lot_id: lot_id.use_date and "%s" % fields.Date.from_string(lot_id.use_date) or '', lot_ids)),
                            'field': prop_line.name.name,
                            'attrs': False, 'image': False, 'sequence': prop_line.name.sequence,
                            'type': prop_line.name.type_fields,
                            'currency_id': currency_id,
                            'color': color}
                    elif lot_ids and not isinstance(lot_ids, (str,)) and prop_line.name.type_fields == 'gs1':
                        res[prop_line.name.name] = {
                            'value': '-'.join(map(lambda lot_id: lot_id and lot_id.hr_gs1 or '', lot_ids)),
                            'field': prop_line.name.name,
                            'attrs': False, 'image': False,
                            'sequence': prop_line.name.sequence,
                            'type': prop_line.name.type_fields,
                            'currency_id': self._get_default_currency_id(prop_line, prop_line.name)}
                    elif lot_ids and isinstance(lot_ids, (str,)):
                        res[prop_line.name.name] = {
                            'value': lot_ids and '-'.join([prefix + x + suffix for x in lot_ids]) or '',
                            'field': prop_line.name.name,
                            'attrs': False, 'image': False, 'sequence': prop_line.name.sequence,
                            'type': prop_line.name.type_fields,
                            'currency_id': currency_id,
                            'color': color}
                    elif not line and codes and prop_line.name.type_fields == 'pricelist':
                        value = codes and ", ".join(map(str, codes))
                        res[prop_line.name.name] = {'value': value,
                                                    'field': prop_line.name.name,
                                                    'attrs': prop_line.with_context(
                                                        force_display=True).type_display_attrs,
                                                    'image': prop_line.image_128, 'sequence': prop_line.name.sequence,
                                                    'type': prop_line.name.type_fields,
                                                    'currency_id': currency_id,
                                                    'color': color}
                    elif line and prop_line.name.type_fields == 'pricelist':
                        prop_line.type_field_model = line._name
                        if codes:
                            value = ", ".join(codes)
                        elif not codes and 'code' in line._fields:
                            value = line.code
                        else:
                            prop_line.model_obj_id = line.id
                            prop_line.type_field_ttype = 'many2one'
                            prop_line.type_field_name = 'pricelist_rule_id'
                            value = prop_line.with_context(dict(ctx, force_display=True)).type_display
                        res[prop_line.name.name] = {'value': value,
                                                    'field': prop_line.name.name,
                                                    'attrs': prop_line.with_context(
                                                        force_display=True).type_display_attrs,
                                                    'image': prop_line.image_128, 'sequence': prop_line.name.sequence,
                                                    'type': prop_line.name.type_fields,
                                                    'currency_id': currency_id,
                                                    'color': color}
                    else:
                        res[prop_line.name.name] = {'value': prop_line.with_context(
                            dict(ctx, force_display=True, force_model=line)).type_display,
                                                    'field': prop_line.name.name,
                                                    'attrs': prop_line.with_context(
                                                        force_display=True).type_display_attrs,
                                                    'image': prop_line.image_128, 'sequence': prop_line.name.sequence,
                                                    'type': prop_line.name.type_fields,
                                                    'currency_id': currency_id,
                                                    'color': color}

        for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields):
            if properties_print and g in print_static_ids:
                color = 0
                prop_lines = self._get_statistic_prop(product)
                # _logger.info(f'Static properties print: {product}-{g}-{prop_lines}')

                if not prop_lines:
                    continue

                for prop_line in prop_lines:
                    if not prop_line:
                        continue

                    field = static_properties_obj.fields_get(g)[g]
                    field_value = getattr(prop_line.with_context(dict(ctx, force_display=True)), g)

                    if not field_value:
                        continue

                    if field['type'] == 'many2one':
                        field_relation = field_value
                        field_name = 'id'
                        if 'color' in field_relation._fields:
                            color = getattr(field_relation, 'color')
                        if 'name' in field_relation._fields:
                            field_name = 'name'
                        if 'display_name' in field_relation._fields:
                            field_name = 'display_name'
                        field_value = getattr(field_relation.with_context(dict(ctx, force_display=True)), field_name)
                        try:
                            field_value_new = safe_eval(field_value, {'object': line, 'context': rcontext})
                        except Exception as e:
                            _logger.warning("The field eval not supported this syntax's error %s" % e)
                            field_value_new = False
                        if field_value_new:
                            field_value = field_value_new

                    res[field['string']] = {'value': field_value,
                                            'field': g,
                                            'attrs': False,
                                            'image': False,
                                            'sequence': prop_line.sequence,
                                            'type': field['type'],
                                            'currency_id': self._get_default_currency_id(prop_line, g),
                                            'color': color}
        for k, v in dict(sorted(res.items(), key=lambda x: x[1]['sequence'])).items():
            if v['value']:
                ret.append({'label': k, 'value': v})
        return ret

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('type_url'):
                vals['type_url'] = _clean_website(vals['type_url'])
        return super(ProductPropertiesType, self).create(vals_list)

    def write(self, vals):
        if vals.get('type_url'):
            vals['type_url'] = _clean_website(vals['type_url'])
        return super(ProductPropertiesType, self).write(vals)
