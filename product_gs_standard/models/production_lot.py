# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from datetime import datetime
from odoo.osv import expression
from odoo import api, fields, models, _
from .hibc import HIBC
from .gs1 import GS1

import logging
_logger = logging.getLogger(__name__)


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    gs1 = fields.Char("GS1 (GTIN + AI(s)", index=True, compute="_get_from_name_gs", inverse="_set_from_gs", search='_search_gs1', store=True)
    hibc = fields.Char("Health Inventory Barcode", index=True, compute="_get_from_name_hibc", inverse="_set_from_hibc", search='_search_hibc', store=True)


    @api.multi
    @api.depends('name', 'use_date', 'product_id.barcode', 'product_id.tracking')
    def _get_from_name_gs(self):
        for record in self:
            if record.name and len(record.product_id.barcode or []) in (8, 12, 13, 14) and record.product_id.tracking == 'lot':
                if record.use_date:
                    record.gs1 = "01%s17%s10%s" % (record.product_id.barcode, datetime.strptime(record.use_date, "%Y%m%d"), record.name)
                else:
                    record.gs1 = "01%s10%s" % (record.product_id.barcode, record.name)
            elif record.name and len(record.product_id.barcode or []) in (8, 12, 13, 14) and record.product_id.tracking in ('serial', 'serialrange'):
                if record.use_date:
                    record.gs1 = "01%s17%s21%s" % (record.product_id.barcode, datetime.strptime(record.use_date, "%Y%m%d"), record.name)
                else:
                    record.gs1 = "01%s21%s" % (record.product_id.barcode, record.name)
            elif record.product_id.tracking == 'lot':
                record.gs1 = "10%s" % record.name
            elif record.product_id.tracking in ('serial', 'serialrange'):
                record.gs1 = "21%s" % record.name

    @api.multi
    @api.onchange('gs1')
    @api.depends('name', 'use_date', 'product_id.barcode', 'product_id.tracking', 'product_id.product_tmpl_id')
    def onchange_gs1(self):
        self.ensure_one()
        _bcde_n = re.sub(r'[^A-Za-z0-9]+', '', self.gs1)
        #_logger.info("GS1: %s:%s" % (_bcde_n, re.match(r'^(01)[0-9]{14}(10\w*|17[0-9]{6})(10\w*|17[0-9]{6})$', _bcde_n)))
        if re.match(r'^(01)[0-9]{14}(10\w*|17[0-9]{6})(10\w*|17[0-9]{6})$', _bcde_n) \
            or re.match(r'^(01)[0-9]{14}(21\w*|17\d{6})(21\w*|17\d{6})$', _bcde_n) \
            or re.match(r'^(01)[0-9]{14}(21\w*)$', _bcde_n) \
            or re.match(r'^(01)[0-9]{14}(10\w*)$', _bcde_n):
            _gs1 = GS1(_bcde_n)
            data = _gs1.parse()
            #_logger.info("GS1 %s" % data)
            value = {}
            if data:
                value['gs1'] = self.gs1
                value['name'] = data['lot_number']
                if data['expiration_date']:
                    value['use_date'] = data['expiration_date']
                product_template = self.product_id.product_tmpl_id
                #_logger.info("TEMPLATE %s:" % product_template)
                if product_template.is_product_variant:
                    product_template.write({'barcode': data['gtin_number']})
                else:
                    self.product_id.write({'barcode': data['gtin_number']})
            else:
                value['gs1'] = False
            if value:
                self.update(value)
        else:
            return


    @api.multi
    @api.depends('name', 'use_date', 'product_id.barcode', 'product_id.tracking')
    def _get_from_name_hibc(self):
        for record in self:
            record.hibc = False

    @api.multi
    @api.onchange('hibc')
    @api.depends('name', 'use_date', 'product_id.barcode', 'product_id.tracking', 'product_id.product_tmpl_id')
    def onchange_hibc(self):
        self.ensure_one()
        _hibc = HIBC(self.hibc)
        data = _hibc.parse()
        value = {}
        if data:
            value['hibc'] = self.hibc
            value['name'] = data['lot_number']
            if data['expiration_date']:
                value['use_date'] = data['expiration_date']
                product_template = self.product_id.product_tmpl_id
                if product_template.is_product_variant:
                    product_template.write({'barcode': data['gtin_number']})
                else:
                    self.product_id.write({'barcode': data['gtin_number']})
        else:
            value['hibc'] = False
        if value:
            self.update(value)


    @api.multi
    @api.depends('name', 'use_date', 'product_id.barcode', 'product_id.tracking', 'product_id.product_tmpl_id')
    def _set_from_gs(self):
        for record in self:
            if not record.gs1: continue
            _bcde_n = re.sub(r'[^A-Za-z0-9]+', '', self.gs1)
            if re.match(r'^(01)[0-9]{14}(10\w*|17[0-9]{6})(10\w*|17[0-9]{6})$', _bcde_n) \
                    or re.match(r'^(01)[0-9]{14}(21\w*|17\d{6})(21\w*|17\d{6})$', _bcde_n) \
                    or re.match(r'^(01)[0-9]{14}(21\w*)$', _bcde_n) \
                    or re.match(r'^(01)[0-9]{14}(10\w*)$', _bcde_n): continue


    @api.multi
    def _set_from_hibc(self):
        for record in self:
            if not record.hibc: continue
            if re.match(r'(^[+])\w(\d{3})([\w\d]*)/(\d{6})(\d*)([\w\d_+$\-.\s%]*)$', record.hibc): continue


    def _search_gs1(self, operator, value):
        domain = [('gs1', operator, value)]
        _bcde_n = re.sub(r'[^A-Za-z0-9]+', '', value)
        if re.match(r'^(01)[0-9]{14}(10\w*|17[0-9]{6})(10\w*|17[0-9]{6})$', _bcde_n) \
                or re.match(r'^(01)[0-9]{14}(21\w*|17\d{6})(21\w*|17\d{6})$', _bcde_n) \
                or re.match(r'^(01)[0-9]{14}(21\w*)$', _bcde_n) \
                or re.match(r'^(01)[0-9]{14}(10\w*)$', _bcde_n)\
                or re.match(r'^(01)[0-9]{14}$', _bcde_n):
            _gs1 = GS1(_bcde_n)
            data = _gs1.parse()
            if data and data['gtin_number']:
                domain = [('barcode', operator, data['gtin_number'])]
            if data and data['expiration_date']:
                domain += [('use_date', operator, data['expiration_date'])]
            if data and data['lot_number']:
                domain += [('name', operator, data['lot_number'])]
        elif re.match(r'(^[+])\w(\d{3})([\w\d]*)/(\d{6})(\d*)([\w\d_+$\-.\s%]*)$', value):
            _hibc = HIBC(value)
            data = _hibc.parse()
        return domain

    def _search_hibc(self, operator, value):
        return [('hibc', operator, value)]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('gs1', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()
