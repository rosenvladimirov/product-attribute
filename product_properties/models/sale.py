# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


def name_boolean_print(id):
    return 'print_' + str(id)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    #use_product_description = fields.Boolean(default=True)
    use_product_properties = fields.Selection([
        ('description', _('Use descriptions')),
        ('properties', _('Use properties')),],
        string="Type product description",
        help='Choice type of the view for product description',
        default="description")
    print_properties = fields.One2many('product.properties.print', 'order_id', 'Print properties')
    #print_properties = fields.One2many('product.properties.print', 'partner_id', related='partner_id.print_properties', string='Print properties')
    products_properties = fields.Html('Products properties', compute="_get_products_properties")
    category_print_properties = fields.Many2one('product.properties.print.category', 'Default Print properties category')
    product_prop_static_id = fields.Many2one("product.properties.static", 'Static Product properties')
    invoice_sub_type = fields.Many2one(related="product_prop_static_id.invoice_sub_type")

#    @api.model
#    def fields_get(self, allfields=None, attributes=None):
#        res = super(SaleOrder, self).fields_get(allfields, attributes=attributes)
#        static_properties_obj = self.env['product.properties.static']
#        dinamic_properties_obj = self.env['product.properties.category']
#        # boolean group fields
#        for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj.with_context(lang="en")._fields):
#            field = static_properties_obj.fields_get(g)[g]
#         if allfields and 'print_' + g.lower().replace(" ", "_") not in allfields:
#                continue
#            res['print_' + g.lower().replace(" ", "_")] = {
 #               'type': 'boolean',
  #              'string': field["string"],
#                'compute': "_get_print_field",
#                'exportable': False,
#                'selectable': False,
#            }
#        for categ in dinamic_properties_obj.search([]):
#            for line in categ.lines_ids:
#                for g in line.with_context(lang="en"):
#                    if allfields and 'print_' + g.name.name.lower().replace(" ", "_")+"_%d" % g.name.id not in allfields:
#                        continue
#                    res['print_' + g.name.name.lower().replace(" ", "_")+"_%d" % g.name.id] = {
#                        'type': 'boolean',
#                        'string': g.name.name,
#                        'compute': "_get_print_field",
#                        'exportable': False,
 #                       'selectable': False,
#                    }
        #_logger.info("FIELDS %s" % res)
#        return res

    @api.multi
    def _get_print_field(self):
        fields = []
        static_properties_obj = self.env['product.properties.static']
        dinamic_properties_obj = self.env['product.properties.category']
        for categ in dinamic_properties_obj.search([]):
            for line in categ.lines_ids:
                for g in line.with_context(lang="en"):
                    fields.append('print_' + g.name.name.lower().replace(" ", "_")+"_%d" % g.name.id)
        for record in self.print_properties:
            for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj.with_context(lang="en")._fields):
                setattr(self, 'print_' + g.lower().replace(" ", "_"), record.print)
            for field in fields:
                parts = field.split("_")
                if record.name == parts[1] and  record.name.id == int(parts[2]):
                    setattr(self, field, record.print)

   # @api.multi
   # def read(self, fields=None, load='_classic_read'):
        #static_properties_obj = self.env['product.properties.static']
        #dinamic_properties_obj = self.env['product.properties.category']
        #pfields = []
        #for categ in dinamic_properties_obj.search([]):
          #  for line in categ.lines_ids:
           #     for g in line.with_context(lang="en"):
            #        pfields.append('print_' + g.name.name.lower().replace(" ", "_")+"_%d" % g.name.id)
        #fields1 = fields or list(self.fields_get())
       # #_logger.info("FIELDS %s" % list(self.fields_get()))
        other_fields = {}
       # print_fields = {}
        #for k,v in self.fields_get().items():
           # if v.get('compute') and v['compute'] != '_get_print_field':
          #      other_fields[k] = v
          #  else:
         #       print_fields[k] = v
        #if print_fields:
         #   pother_fields = list(other_fields)
        #else:
         #   pother_fields = fields
        #res = super(SaleOrder, self).read(pother_fields, load=load)
        #_logger.info("RES %s" % res)
        #for line in res:
            #_logger.info("LINE %s" % line)
         #   for values in line["print_properties"]:
          #      row = self.print_properties.browse(values)
           #     for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj.with_context(lang="en")._fields):
         #           line['print_' + g.lower().replace(" ", "_")] = row.print
         #       for field in pfields:
          #          parts = field.split("_")
           #         if row.name == parts[1] and  row.name.id == int(parts[2]):
            #            line[field] = row.print
        #return res

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for order in self:
            if order.partner_id.print_properties:
                values = []
                for line in order.partner_id.print_properties:
                    compare = order.print_properties.filtered(lambda r: r.name == line.name)
                    if compare:
                        values.append((1, compare.id, {'name': line.name, 'print': line.print}))
                    else:
                        values.append((0, False, {'name': line.name, 'print': line.print, 'order_id': order.id}))
                if values:
                    order.update({'print_properties': values})
                else:
                    order.update({'print_properties': False})
        return super(SaleOrder, self).onchange_partner_id()

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        rcontext['doc'] = self
        result['html'] = self.env.ref(
            'product_properties.report_saleorder_html').with_context(context).render(
                rcontext)
        return result

    @api.multi
    def _get_products_properties(self):
        for rec in self:
            if len(rec.order_line.ids) > 0:
                rec.products_properties = rec._get_html()['html']

    @api.multi
    def remove_all_print_properties(self):
        for record in self:
            record.print_properties =  False

    @api.multi
    def set_all_print_properties(self):
        print_ids = False
        for record in self:
            record.print_properties = self.env['product.properties'].set_all_print_properties(record, record.order_line)
            if record.invoice_ids:
                for inv in record.invoice_ids:
                    inv.set_all_print_properties()
            if record.picking_ids:
                for picking in record.picking_ids:
                    picking.set_all_print_properties()

    @api.multi
    def set_partner_print_properties(self):
        for record in self:
            print_properties = []
            partner = record.partner_id.parent_id and record.partner_id.parent_id or record.partner_id
            partner_static_print_ids = [x.static_field for x in partner.print_properties if x.print and x.static_field]
            if partner.print_properties and not record.print_properties:
                print_properties += [(0, False, {'name': x.name.id, 'order_id': self.id, 'print': True, 'sequence': x.sequence}) for x in partner.print_properties if x.name and not x.static_field]
                if partner_static_print_ids:
                    print_properties += [(0, False, {'static_field': x, 'order_id': self.id, 'print': True, 'sequence': 9999}) for x in partner_static_print_ids]
                record.print_properties = print_properties

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        vals = self.env['product.properties.static'].static_property_data(res, vals)
        return res

    @api.multi
    def write(self, vals):
        if 'product_prop_static_id' not in vals:
            for record in self:
                vals = self.env['product.properties.static'].static_property_data(record, vals)
        return super(SaleOrder, self).write(vals)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    has_propertis = fields.Boolean(compute="_get_has_propertis")

    def _get_has_propertis(self):
        for rec in self:
            rec.has_propertis = len(rec.order_id.print_properties.ids) > 0

    @api.multi
    def _prepare_invoice_line(self, qty):
        vals = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        if self.order_id.print_properties:
            vals['print_properties'] = self.order_id.print_properties.ids
        return vals
