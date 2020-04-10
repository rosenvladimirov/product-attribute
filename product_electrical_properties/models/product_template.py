# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, except_orm

import logging
_logger = logging.getLogger(__name__)

LIFE_TIME = {'msl5a': 1,
             'msl5': 2,
             'msl4': 4,
             'msl3': 7,
             'msl2a': 28,
             'msl2': 365,
            }


class ProductProduct(models.Model):
    _inherit = "product.template"

    @api.multi
    def _package_type(self):
        for record in self:
            if record.electrical_properties_id:
                package = ''
                for package_type in record.electrical_properties_ids:
                    if package_type.type_fields == 'package':
                        package = package_type.type_package_id.name
                        break
                record.electrical_properties_package = package
                msl = ''
                for package_type in record.electrical_properties_ids:
                    if package_type.type_fields == 'msl':
                        msl = package_type.type_msl
                        break
                record.electrical_properties_msl = msl

            else:
                record.electrical_properties_package = ''
                record.electrical_properties_msl = ''

    def _get_default_electrical_properties_ids(self):
        ret = []
        for rec in self.electrical_properties_id.lines_ids:
            res = self.env["product.electrical.properties"].create({
                                                              'product_tmpl_id': self.id,
                                                              'sequence': rec.sequence,
                                                              'name': rec.name.id,
                                                              'type_fields': rec.type_fields,
                                                              'type_char': rec.type_char,
                                                              'type_int': rec.type_int,
                                                              'type_int_second': rec.type_int_second,
                                                              'type_boolean': rec.type_boolean,
                                                              'type_package_id': rec.type_package_id.id,
                                                              'dimensions_x': rec.dimensions_x,
                                                              'dimensions_y': rec.dimensions_y,
                                                              'dimensions_z': rec.dimensions_z,
                                                              'type_msl': rec.type_msl,
                                                              'type_uom_id': rec.type_uom_id.id,
                                                              'image': rec.image,
                                                            })
            ret.append(res.id)
        return ret

    electrical_properties_id = fields.Many2one("product.electrical", string="Categorie Electrical properties")
    electrical_properties_ids = fields.Many2many("product.electrical.properties",
        string='Electrical properties', default=_get_default_electrical_properties_ids)
    electrical_properties_package = fields.Char("Package/Socket type", compute='_package_type', store=False)
    electrical_properties_msl = fields.Char("Moisture sensitivity level", compute='_package_type', store=False)

    @api.model
    def _get_life_time(self, msl):
        return LIFE_TIME.get(msl, False)

    @api.multi
    def write(self, vals):
        if 'electrical_properties_ids' not in vals and'electrical_properties_id' in vals:
            for product_template in self:
                ret = []
                pl = self.env['product.electrical'].browse([vals['electrical_properties_id']])
                if pl:
                    self.write({'electrical_properties_ids': [(2, x.id) for x in record.electrical_properties_ids]})
                    for rec in pl.lines_ids:
                        res = self.env["product.electrical.properties"].create({
                                                          'product_tmpl_id': product_template.id,
                                                          'sequence': rec.sequence,
                                                          'name': rec.name.id,
                                                          'type_fields': rec.type_fields,
                                                          'type_char': rec.type_char,
                                                          'type_int': rec.type_int,
                                                          'type_int_second': rec.type_int_second,
                                                          'type_boolean': rec.type_boolean,
                                                          'type_package_id': rec.type_package_id.id,
                                                          'dimensions_x': rec.dimensions_x,
                                                          'dimensions_y': rec.dimensions_y,
                                                          'dimensions_z': rec.dimensions_z,
                                                          'type_msl': rec.type_msl,
                                                          'type_uom_id': rec.type_uom_id.id,
                                                          'image': rec.image,
                                                        })
                        ret.append(res.id)
                    vals['electrical_properties_ids'] = [(4, x) for x in ret]
        return super(ProductProduct, self).write(vals)

    @api.onchange('electrical_properties_msl')
    def _onchange_electrical_properties_msl(self):
        return {'value': {'life_time': self._get_life_time(self.electrical_properties_msl)}}

    @api.onchange('electrical_properties_id')
    def _onchange_electrical_properties_id(self):
        self.write({'electrical_properties_ids': [(2, x.id) for x in self.electrical_properties_ids]})
        res = [(4, x) for x in self._get_default_electrical_properties_ids()]
        #self.electrical_properties_ids = res
        return {'value': {'electrical_properties_ids': res}}
