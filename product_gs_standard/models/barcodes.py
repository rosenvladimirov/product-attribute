# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import tools, models, fields, api, _
from .hibc import HIBC
from .gs1 import GS1

import logging
_logger = logging.getLogger(__name__)


class BarcodeNomenclature(models.Model):
    _inherit = 'barcode.nomenclature'

    def check_encoding(self, barcode, encoding, pattern=None):
        if encoding in ('gs1', 'udi'):
            if re.match(r'^(01)[0-9]{14}(11[0-9]{6}|10\w*|17[0-9]{6}|17[0-9]{8})(10\w*|17[0-9]{6}|17[0-9]{8}|240\w*)$', barcode) \
                    or re.match(r'^(01)[0-9]{14}(21\w*|17\d{6}|17\d{8})(21\w*|17\d{6}|17\d{8})$', barcode) \
                    or re.match(r'^(01)[0-9]{14}(21\w*)$', barcode) \
                    or re.match(r'^(01)[0-9]{14}(10\w*)$', barcode) \
                    or re.match(r'^(01)[0-9]{14}(240\w*)$', barcode):
                return True
        elif encoding == 'hibc':
            if re.match(r'^(01)[0-9]{14}(10\w*|17[0-9]{6}|17[0-9]{8})(10\w*|17[0-9]{6}|17[0-9]{8})$', barcode) \
                    or re.match(r'^(01)[0-9]{14}(21\w*|17\d{6})(21\w*|17\d{6})$', barcode) \
                    or re.match(r'^(01)[0-9]{14}(21\w*)$', barcode) \
                    or re.match(r'^(01)[0-9]{14}(10\w*)$', barcode):
                return True
        elif encoding == 'europlacerlot':
            return barcode[:1].isdigit() == False
        elif encoding == 'pattern' and pattern:
            match = re.compile(pattern)
            if match.match(barcode):
                return True
        else:
            return super(BarcodeNomenclature, self).check_encoding(barcode, encoding)

    def match_pattern(self, barcode, pattern):
        match = {
            "value": 0,
            "base_code": barcode,
            "match": False,
        }
        _bcde_n = re.sub(r'[^A-Za-z0-9]+', '', barcode)
        #_logger.info("CHECK MATCH %s" % _bcde_n)
        if re.match(r'^(01)[0-9]{14}(11[0-9]{6}|10\w*|17[0-9]{6}|17[0-9]{8})(|17[0-9]{6}|17[0-9]{8}|10\w*|240\w*)$', _bcde_n) \
            or re.match(r'^(01)[0-9]{14}(21\w*|17\d{6}|17\d{8})(21\w*|17\d{6}|17\d{8})$', _bcde_n) \
            or re.match(r'^(01)[0-9]{14}(21\w*)$', _bcde_n) \
            or re.match(r'^(01)[0-9]{14}(10\w*)$', _bcde_n) \
            or re.match(r'^(01)[0-9]{14}(240\w*)$', _bcde_n):
            _gs1 = GS1(_bcde_n)
            data = _gs1.parse()
            #_logger.info("Math %s" % data)
            if data:
                match['match'] = True
                match['base_code'] = data['gtin_number']
                match['lot_number'] = data['lot_number']
                match['default_code'] = data['default_code']
                if data['expiration_date']:
                    match['use_date'] = data['expiration_date']
                return match
        if not match['match']:
            return super(BarcodeNomenclature, self).match_pattern(barcode, pattern)

    def parse_barcode(self, barcode):
        parsed_result = {
            'encoding': '',
            'type': 'error',
            'sub_type': 'product',
            'code': barcode,
            'base_code': barcode,
            'value': 0,
        }

        rules = []
        for rule in self.rule_ids:
            rules.append({'type': rule.type, 'sub_type': rule.sub_type, 'encoding': rule.encoding, 'sequence': rule.sequence, 'pattern': rule.pattern, 'alias': rule.alias})

        for rule in sorted(rules, key=lambda k: k['sequence']):
            cur_barcode = barcode
            if rule['encoding'] == 'ean13' and self.check_encoding(barcode,'upca') and self.upc_ean_conv in ['upc2ean','always']:
                cur_barcode = '0'+cur_barcode
            elif rule['encoding'] == 'upca' and self.check_encoding(barcode,'ean13') and barcode[0] == '0' and self.upc_ean_conv in ['ean2upc','always']:
                cur_barcode = cur_barcode[1:]

            if not self.check_encoding(barcode,rule['encoding'], pattern=rule['pattern']):
                continue

            match = self.match_pattern(cur_barcode, rule['pattern'])
            _logger.info("MATCH %s:%s" % (match, rule))
            if match['match']:
                if rule['type'] == 'alias':
                    barcode = rule['alias']
                    parsed_result['code'] = barcode
                elif rule['type'] == 'product' and rule['sub_type'] in ('component', 'product'):
                    parsed_result['encoding'] = rule['encoding']
                    parsed_result['type'] = rule['type']
                    parsed_result['sub_type'] = rule['sub_type']
                    parsed_result['value'] = match['value']
                    parsed_result['code'] = cur_barcode
                    parsed_result['lot'] = False
                    parsed_result['use_date'] = False
                    parsed_result['base_code'] = match['base_code']
                    return parsed_result

                elif rule['type'] == 'lot' and rule['sub_type'] in ('component', 'product'):
                    parsed_result['encoding'] = rule['encoding']
                    parsed_result['type'] = rule['type']
                    parsed_result['sub_type'] = rule['sub_type']
                    parsed_result['value'] = match['value']
                    parsed_result['code'] = cur_barcode
                    parsed_result['lot'] = (rule['encoding'] == 'europlacerlot') and match['base_code'][1:] or match['base_code']
                    parsed_result['base_code'] = False
                    return parsed_result

                elif rule['type'] == 'lot' and rule['encoding'] == 'europlacerlot':
                    parsed_result['encoding'] = rule['encoding']
                    parsed_result['type'] = rule['type']
                    parsed_result['sub_type'] = rule['sub_type']
                    parsed_result['value'] = match['value']
                    parsed_result['code'] = cur_barcode
                    parsed_result['lot'] = match['base_code'][1:]
                    parsed_result['base_code'] = False
                    return parsed_result

                elif rule['type'] == 'lot' and rule['encoding'] in ('gs1', 'udi', 'hibc') and match['lot_number'] is not None:
                    parsed_result['encoding'] = rule['encoding']
                    parsed_result['type'] = rule['type']
                    parsed_result['sub_type'] = rule['sub_type']
                    parsed_result['code'] = cur_barcode
                    parsed_result['base_code'] = match['base_code']
                    parsed_result['lot'] = match['lot_number']
                    parsed_result['use_date'] = match.get('use_date') and match['use_date'] or False
                    return parsed_result

                elif rule['type'] == 'lot' and rule['encoding'] in ('gs1', 'udi', 'hibc') and match['lot_number'] is None:
                    parsed_result['encoding'] = rule['encoding']
                    parsed_result['type'] = 'product'
                    parsed_result['sub_type'] = rule['sub_type']
                    parsed_result['code'] = cur_barcode
                    parsed_result['base_code'] = match['base_code']
                    parsed_result['default_code'] = match['default_code']
                    parsed_result['lot'] = match['lot_number']
                    parsed_result['use_date'] = match.get('use_date') and match['use_date'] or False
                    return parsed_result

                elif rule['type'] == 'product' and rule['encoding'] in ('gs1', 'udi', 'hibc'):
                    parsed_result['encoding'] = rule['encoding']
                    parsed_result['type'] = rule['type']
                    parsed_result['sub_type'] = rule['sub_type']
                    parsed_result['code'] = cur_barcode
                    parsed_result['base_code'] = match['base_code']
                    parsed_result['lot'] = match['lot_number']
                    parsed_result['use_date'] = match.get('use_date') and match['use_date'] or False
                    return parsed_result

                else:
                    parsed_result['encoding'] = rule['encoding']
                    parsed_result['type'] = rule['type']
                    parsed_result['sub_type'] = rule['sub_type']
                    parsed_result['value'] = match['value']
                    parsed_result['code'] = cur_barcode
                    parsed_result['lot'] = False
                    parsed_result['use_date'] = False
                    if rule['encoding'] == "ean13":
                        parsed_result['base_code'] = self.sanitize_ean(match['base_code'])
                    elif rule['encoding'] == "upca":
                        parsed_result['base_code'] = self.sanitize_upc(match['base_code'])
                    else:
                        parsed_result['base_code'] = match['base_code']
                    return parsed_result
        return parsed_result


class BarcodeRule(models.Model):
    _inherit = 'barcode.rule'

    encoding = fields.Selection(selection_add=[
            ('gs1', 'GTIN+AI(n)'),
            ('udi', 'Unique Device Identification (UDI)'),
            ('hibc', 'Health Industry Bar Code Standard'),
            ('europlacerlot', 'LOT/SN for Europlacer'),
            ('pattern', 'Pattern mode'),
        ])

    sub_type = fields.Selection([
                ('component', 'MRP Component'),
                ('product', 'MRP Product'),
                ('momp', 'MRP Manufacture order'),
                ('wo', 'MRP Workorder'),
                ], string="Application use")
