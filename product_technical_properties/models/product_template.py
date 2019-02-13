# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, except_orm

import logging
_logger = logging.getLogger(__name__)

LIFE_TIME = {'class1': 3650,
             'class2': 3650,
            }


class ProductProduct(models.Model):
    _inherit = "product.template"

    @api.multi
    def _package_type(self):
        for record in self:
            if record.technical_properties_id:
                package = ''
                for package_type in record.technical_properties_ids:
                    if package_type.type_fields == 'package':
                        package = package_type.type_package_id.name
                        break
                record.technical_properties_package = package
                msl = ''
                for package_type in record.technical_properties_ids:
                    if package_type.type_fields == 'tank':
                        msl = package_type.type_tank
                        break
                record.technical_properties_tank = tank

            else:
                record.technical_properties_package = ''
                record.technical_properties_tank = ''

    def _get_default_technical_properties_ids(self):
        ret = []
        for rec in self.technical_properties_id.lines_ids:
            res = self.env["product.technical.properties"].create({
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
                                                              'type_euro': rec.type_euro,
                                                              'type_tank': rec.type_tank,
                                                              'volume': rec.volume,
                                                              'type_uom_id': rec.type_uom_id.id,
                                                              'image': rec.image,
                                                            })
            ret.append(res.id)
        return ret

    technical_properties_id = fields.Many2one("product.technical", string="Categorie Technical properties")
    technical_properties_ids = fields.Many2many("product.technical.properties",
        string='Electrical properties', default=_get_default_technical_properties_ids)
    technical_properties_package = fields.Char("Package/Socket type", compute='_package_type', store=False)
    technical_properties_tank = fields.Char("Moisture sensitivity level", compute='_package_type', store=False)
    type_power = fields.Integer("Value for Power low threshold")
    type_power_second = fields.Integer("Value for Power high threshold")
    volume = fields.Float(related="type_tank_id.volume", string="Volume (L)")

    @api.model
    def _get_life_time(self, msl):
        return LIFE_TIME.get(msl, False)

    @api.multi
    def write(self, vals):
        if 'technical_properties_ids' not in vals and 'technical_properties_id' in vals:
            for product_template in self:
                ret = []
                pl = self.env['product.electrical'].browse([vals['technical_properties_id']])
                if pl:
                    self.write({'technical_properties_ids': [(2, x.id) for x in record.electrical_properties_ids]})
                    for rec in pl.lines_ids:
                        res = self.env["product.technical.properties"].create({
                                                          'product_tmpl_id': product_template.id,
                                                          'sequence': rec.sequence,
                                                          'name': rec.name.id,
                                                          'type_fields': rec.type_fields,
                                                          'type_char': rec.type_char,
                                                          'type_int': rec.type_int,
                                                          'type_int_second': rec.type_int_second,
                                                          'type_power': rec.type_power,
                                                          'type_power_second': rec.type_power_second,
                                                          'type_boolean': rec.type_boolean,
                                                          'type_package_id': rec.type_package_id.id,
                                                          'dimensions_x': rec.dimensions_x,
                                                          'dimensions_y': rec.dimensions_y,
                                                          'dimensions_z': rec.dimensions_z,
                                                          'type_tank': rec.type_tank,
                                                          'type_euro': rec.type_euro,
                                                          'type_cars': rec.type_cars,
                                                          'type_uom_id': rec.type_uom_id.id,
                                                          'image': rec.image,
                                                        })
                        ret.append(res.id)
                    vals['technical_properties_ids'] = [(4, x) for x in ret]
        return super(ProductProduct, self).write(vals)

    @api.onchange('technical_properties_msl')
    def _onchange_electrical_properties_msl(self):
        return {'value': {'life_time': self._get_life_time(self.technical_properties_msl)}}

    @api.onchange('electrical_properties_id')
    def _onchange_electrical_properties_id(self):
        self.write({'electrical_properties_ids': [(2, x.id) for x in self.electrical_properties_ids]})
        res = [(4, x) for x in self._get_default_electrical_properties_ids()]
        #self.electrical_properties_ids = res
        return {'value': {'electrical_properties_ids': res}}
