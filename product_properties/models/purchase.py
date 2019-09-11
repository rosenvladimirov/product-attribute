# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    use_product_description = fields.Boolean(default=True)
    print_properties = fields.One2many('product.properties.print.purchase', 'order_id', 'Print poperties')
    products_properties = fields.Html('Products properties', compute="_get_products_properties")


    @api.multi
    def copy(self, default=None):
        new_po = super(PurchaseOrder, self).copy(default=default)
        for line in new_po.order_line:
            seller = line.product_id.with_context(dict(self._context, manufacturer_id=line.manufacturer_id.id))._select_seller(
                partner_id=line.partner_id, quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date(), uom_id=line.product_uom)
            line.date_planned = line._get_date_planned(seller)
        return new_po

    @api.multi
    def _add_supplier_to_product(self):
        # Add the partner in the supplier list of the product if the supplier is not registered for
        # this product. We limit to 10 the number of suppliers for a product to avoid the mess that
        # could be caused for some generic products ("Miscellaneous").
        for line in self.order_line:
            # Do not add a contact as a supplier
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            if partner not in line.product_id.seller_ids.mapped('name') and len(line.product_id.seller_ids) <= 10:
                currency = partner.property_purchase_currency_id or self.env.user.company_id.currency_id
                supplierinfo = {
                    'name': partner.id,
                    'manufacturer_id': line.manufacturer_id.id,
                    'sequence': max(line.product_id.seller_ids.mapped('sequence')) + 1 if line.product_id.seller_ids else 1,
                    'product_uom': line.product_uom.id,
                    'min_qty': 0.0,
                    'price': self.currency_id.compute(line.price_unit, currency, round=False),
                    'currency_id': currency.id,
                    'delay': 0,
                }
                # In case the order partner is a contact address, a new supplierinfo is created on
                # the parent company. In this case, we keep the product name and code.
                seller = line.product_id.with_context(dict(self._context, manufacturer_id= line.manufacturer_id.id))._select_seller(
                    partner_id=line.partner_id,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order[:10],
                    uom_id=line.product_uom)
                if seller:
                    supplierinfo['product_name'] = seller.product_name
                    supplierinfo['product_code'] = seller.product_code
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                try:
                    line.product_id.write(vals)
                except AccessError:  # no write access rights -> just ignore
                    break

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        rcontext['o'] = self
        result['html'] = self.env.ref(
            'product_properties.report_purchaseorder_html').with_context(context).render(
                rcontext)
        return result

    @api.multi
    def _get_products_properties(self):
        for rec in self:
            if len(rec.order_line.ids) > 0:
                rec.products_properties = rec._get_html()['html']


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    manufacturer_id = fields.Many2one("product.manufacturer", "Manufacturer")
    supplierinfo_id = fields.Many2one("product.supplierinfo", "Supplierinfo")
    has_propertis = fields.Boolean(compute="_get_has_propertis")

    def _get_has_propertis(self):
        for rec in self:
            rec.has_propertis = len(rec.order_id.print_properties.ids) > 0

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = super(PurchaseOrderLine, self).onchange_product_id()
        if result.get('domain', False):
            result['domain'].update({'manufacturer_id': ['|', ('product_id', '=', self.product_id.id), ('product_id', '=', False), ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)]})
            #if manufacturer_id.search(['|', ('product_id', '=', self.product_id.id), ('product_id', '=', False), ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)]):
        return result

    @api.onchange('product_qty', 'product_uom', 'manufacturer_id')
    def _onchange_quantity(self):
        if not self.product_id:
            return

        seller = self.product_id.with_context(dict(self._context, manufacturer_id=self.manufacturer_id.id))._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            return

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                             self.product_id.supplier_taxes_id,
                                                                             self.taxes_id,
                                                                             self.company_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id.compute(price_unit, self.order_id.currency_id)

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

        self.price_unit = price_unit
        if seller:
            self.manufacturer_id = seller.manufacturer_id.id
            self.supplierinfo_id = seller.id


class ProductProperties(models.Model):
    _name = "product.properties.print.purchase"
    _description = "Product properties for printing in purchase"

    name = fields.Many2one("product.properties.type", string="Property name", required=True, translate=True)
    print = fields.Boolean('Print')
    order_id = fields.Many2one("purchase.order", string="Purchase order", index=True)

    def get_print_properties(self):
        if use_product_description:
            return False
        return [x.name.id for x in self if x.print]
