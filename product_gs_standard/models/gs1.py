"""
GS1 Barcode parser

Written by: Ian Doarn and Rossen Vladimirov
"""
from re import match, search, sub
from datetime import datetime
from collections import OrderedDict
import sys
# TODO: Comment this file!

import logging
_logger = logging.getLogger(__name__)


class GS1:

    def __init__(self, _barcode_n):
        self.gs1 = self.__sterilize_input(_barcode_n)
        self.gtin_number = None
        self.ean_number = None
        self.lot_number = None
        self.expiration_date = None
        self.production_date = None
        self.ref = None
        self.parse()

#    @classmethod
#    def __verify_gs1(cls, barcode):
#        if match(r'^(01)\d{14}(10\w*|17\d{6}|17\d{8})(10\w*|17\d{6}|17\d{8})$', barcode):
#           return True
#       if match(r'^(01)\d{14}(21\w*|17\d{6}|17\d{8})(21\w*|17\d{6}|17\d{8})$', barcode):
#          return True
#      if match(r'^(01)\d{14}(10\w*)$', barcode):
#          return True
#      return False

    @staticmethod
    def __sterilize_input(_bcde_n):
        return sub(r'[^\w\d]+', '', _bcde_n)

    def __verify_gs1(cls, barcode):
        if match(r'^(01)\d{14}(11\d{6}|10\w*|17\d{6}|17\d{8})(10\w*|17\d{6}|17\d{8}:240\w*)$', barcode):
            return True
        if match(r'^(01)\d{14}(10\w*)$', barcode):
            return True
        if match(r'^(01)\d{14}(21\w*|17\d{6}|17\d{8})(21\w*|17\d{6}|17\d{8})$', barcode):
            return True
        if match(r'^(01)\d{14}(21\w*)$', barcode):
            return True
        if match(r'^(01)\d{14}(240\w*)$', barcode):
            return True
        return False

    @staticmethod
    def __strf_gs1(_bcde_n):
        ean_nbr_m = search('^(01)\d{14}', _bcde_n)
        exp_dte_m = search('(17\d{6})', _bcde_n[16:])
        if match(r'^(01)\d{14}(240\w*)$', _bcde_n):
            lt_ref_m = search('(240\w*)$', _bcde_n[16:])
            return ean_nbr_m.group(0), False, False, lt_ref_m.group(0), False
        elif match(r'^(01)\d{14}(10\w*)(17\d{6})$', _bcde_n):
            lt_nbr_m = search('(?<=^01\d{14})\d*(?=17\d{6})', _bcde_n)
            exp_dte_m = search('(17\d{6})', _bcde_n[16:])
            return ean_nbr_m.group(0), exp_dte_m.group(0), lt_nbr_m.group(0), False, False
        elif match(r'^(01)\d{14}(10\w*)(17\d{6})(11\d{6})$', _bcde_n):
            lt_nbr_m = search('(?<=^01\d{14})\d*(?=17\d{6})', _bcde_n)
            exp_dte_m = search('(17\d{6})', _bcde_n[16:])
            exp_dte_p = search('(11\d{6})', _bcde_n[16:])
            return ean_nbr_m.group(0), exp_dte_m.group(0), lt_nbr_m.group(0), False, exp_dte_p
        elif match(r'^(01)\d{14}(11\d{6})(10\w*)(17\d{6})$', _bcde_n):
            lt_nbr_m = search('(?<=^01\d{14})\d*(?=17\d{6})', _bcde_n)
            exp_dte_m = search('(17\d{6})', _bcde_n[16:])
            exp_dte_p = search('(11\d{6})', _bcde_n[16:])
            return ean_nbr_m.group(0), exp_dte_m.group(0), lt_nbr_m.group(0), False, exp_dte_p
        elif match(r'^(01)\d{14}(10\w*)(17\d{8})$', _bcde_n):
            lt_nbr_m = search('(?<=^01\d{14})\d*(?=17\d{8})', _bcde_n)
            exp_dte_m = search('(17\d{8})', _bcde_n[16:])
            return ean_nbr_m.group(0), exp_dte_m.group(0), lt_nbr_m.group(0), False, False
        elif match(r'^(01)\d{14}(17\d{6})(10\w*)$', _bcde_n):
            lt_nbr_m = search('(?<=17\d{6})(10\w*)$', _bcde_n[16:])
            exp_dte_m = search('(17\d{6})', _bcde_n[16:])
            return ean_nbr_m.group(0), exp_dte_m.group(0), lt_nbr_m.group(0), False, False
        elif match(r'^(01)\d{14}(11\d{6})(17\d{6})(10\w*)$', _bcde_n):
            lt_nbr_m = search('(?<=17\d{6})(10\w*)$', _bcde_n[16:])
            exp_dte_m = search('(17\d{6})', _bcde_n[16:])
            exp_dte_p = search('(11\d{6})', _bcde_n[16:])
            return ean_nbr_m.group(0), exp_dte_m.group(0), lt_nbr_m.group(0), False, exp_dte_p
        elif match(r'^(01)\d{14}(17\d{8})(10\w*)$', _bcde_n):
            lt_nbr_m = search('(?<=17\d{8})(10\w*)$', _bcde_n[16:])
            exp_dte_m = search('(17\d{8})', _bcde_n[16:])
            return ean_nbr_m.group(0), exp_dte_m.group(0), lt_nbr_m.group(0), False, False
        elif match(r'^(01)\d{14}(10\w*)$', _bcde_n):
            lt_nbr_m = search('(10\w*)$', _bcde_n[16:])
            return ean_nbr_m.group(0), False, lt_nbr_m and lt_nbr_m.group(0), False, False
        elif match(r'^(01)\d{14}(21\w*)(17\d{6})$', _bcde_n):
            lt_nbr_m = search('(?<=^01\d{14})\d*(?=17\d{6})', _bcde_n)
            exp_dte_m = search('(17\d{6})', _bcde_n[16:])
            return ean_nbr_m.group(0), exp_dte_m.group(0), lt_nbr_m.group(0), False, False
        elif match(r'^(01)\d{14}(21\w*)(17\d{8})$', _bcde_n):
            lt_nbr_m = search('(?<=^01\d{14})\d*(?=17\d{8})', _bcde_n)
            exp_dte_m = search('(17\d{8})', _bcde_n[16:])
            return ean_nbr_m.group(0), exp_dte_m.group(0), lt_nbr_m.group(0), False, False
        elif match(r'^(01)\d{14}(17\d{6})(21\w*)$', _bcde_n):
            lt_nbr_m = search('(?<=17\d{6})(21\w*)$', _bcde_n[16:])
            exp_dte_m = search('(17\d{6})', _bcde_n[16:])
            return ean_nbr_m.group(0), exp_dte_m.group(0), lt_nbr_m.group(0), False, False
        elif match(r'^(01)\d{14}(17\d{8})(21\w*)$', _bcde_n):
            lt_nbr_m = search('(?<=17\d{8})(21\w*)$', _bcde_n[16:])
            exp_dte_m = search('(17\d{8})', _bcde_n[16:])
            return ean_nbr_m.group(0), exp_dte_m.group(0), lt_nbr_m.group(0), False, False
        elif match(r'^(01)\d{14}(21\w*)$', _bcde_n):
            lt_nbr_m = search('(21\w*)$', _bcde_n[16:])
            return ean_nbr_m.group(0), False, lt_nbr_m and lt_nbr_m.group(0), False, False
        else:
            raise ValueError('Could not read GS1 [{}]. Failed to match regex sequence.'.format(_bcde_n))

    def __parse(self, _bcde_n):
        if self.__verify_gs1(_bcde_n):
            _ean_nbr, _exp_dte, _lt_nbr,  _lt_ref, _prod_dte = self.__strf_gs1(_bcde_n)
            _logger.info("DATE %s:%s:%s" % (_ean_nbr, _exp_dte, _lt_nbr))
            print(_exp_dte)
            if _exp_dte and len(_exp_dte[2:]) == 6:
                _exp_dte =_exp_dte[-2:] == "00" and _exp_dte[:6] + "01" or _exp_dte
                self.expiration_date = _exp_dte and datetime.strptime('20' + _exp_dte[2:], '%Y%m%d').strftime('%Y-%m-%d')
            elif _exp_dte and len(_exp_dte[2:]) == 8:
                try:
                    self.expiration_date = _exp_dte and datetime.strptime(_exp_dte[2:], '%Y%m%d').strftime('%Y-%m-%d')
                except Exception as e:
                    if match(r'^(17\d{6})(10\w*)$', _exp_dte):
                        lt_nbr_m = search('(?<=17\d{6})(10\w*)$', _bcde_n[16:])
                        _lt_nbr = _lt_nbr.group(0)
                        exp_dte_m = search('(17\d{6})',  _exp_dte[:8])
                        self.expiration_date = _exp_dte and datetime.strptime('20' + exp_dte_m.group(0)[2:], '%Y%m%d').strftime('%Y-%m-%d')
                    elif match(r'^(17\d{6})(21\w*)$', _exp_dte):
                        _lt_nbr = search('(?<=17\d{6})(21\w*)$', _bcde_n[16:])
                        _lt_nbr = _lt_nbr.group(0)
                        exp_dte_m = search('(17\d{6})', _exp_dte[:8])
                        #_logger.info("DATE %s:%s" % (_lt_nbr, exp_dte_m))
                        self.expiration_date = _exp_dte and datetime.strptime('20' + exp_dte_m.group(0)[2:], '%Y%m%d').strftime('%Y-%m-%d')
            self.ean_number = _ean_nbr[0:2]
            self.gtin_number = _ean_nbr[2:16]
            self.lot_number = _lt_nbr and _lt_nbr[2:] or None
            self.ref = _lt_ref and _lt_ref[2:] or None
            self.production_date = _prod_dte and _prod_dte[2:] or None
        else:
            raise ValueError('Invalid GS1 [{}]'.format(self.gs1))

    def parse(self):
        self.__parse(self.gs1)

        data = {'barcode': self.gs1,
                'gtin_number': self.gtin_number,
                'ean_number': self.ean_number,
                'lot_number': self.lot_number,
                'default_code': self.ref,
                'expiration_date': self.expiration_date or ''}

        return OrderedDict(data)
