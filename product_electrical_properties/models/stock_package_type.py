# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class PackageType(models.Model):
    _inherit = 'stock.package.type'

    package_identifier = fields.Selection([
        ('R', 'Reel Package'),
        ('T', 'Tape Package'),
        ('B', 'Bulk Package')
    ], string='Detector package',
        help='Reel, Tape or Bulk package'
    )
    quantity_code = fields.Selection([
        ('1K', '1000 pcs'),
        ('2K', '2000 pcs'),
        ('3K', '3000 pcs'),
        ('5K', '5000 pcs'),
        ('10K', '10000 pcs'),
        ('20K', '20000 pcs'),
    ], string='Quantity Code'
    )

    dimensions = fields.Selection(
        [
            ('8', '8 mm'),
            ('12', '12 mm'),
            ('16', '16 mm'),
            ('24', '24 mm'),
            ('32', '32mm'),
        ],
        string='Tape Width',
        help='Standard EIA-481 carrier tape width'
    )
    component_orientation = fields.Selection([
        ('c1', 'Quadrant 1 (C1)'),
        ('c2', 'Quadrant 2 (C2)'),
        ('c3', 'Quadrant 3 (C3)'),
        ('c4', 'Quadrant 4 (C4)'),
    ],
        string='Component Orientation (EIA-481)'
    )
    sprocket_holes = fields.Selection(
        [
        ('10', '10 holes (40mm)'),
        ('25', '25 holes (100mm)'),
        ('50', '50 holes (200mm)'),
        ('100', '100 holes (400mm)'),
        ],
        string='Sprocket Holes Count',
        help='Number of sprocket holes per section'
    )
    reel_diameter = fields.Selection([
        ('178', '178mm (7")'),
        ('330', '330mm (13")'),
    ], string='Reel Diameter')

    cover_tape_width = fields.Float(
        string='Cover Tape Width',
        help='Width of the cover tape in millimeters'
    )

    cavity_dimensions = fields.Char(
        string='Cavity Dimensions',
        help='Dimensions in format AxBxK (width x length x depth) in mm'
    )

    components_per_reel = fields.Integer(
        string='Components per Reel',
        help='Number of components that can be stored on one reel'
    )

    pitch = fields.Float(
        string='Component Pitch',
        help='Distance between component cavities in mm'
    )

    tape_material = fields.Selection([
        ('ps', 'Polystyrene'),
        ('pvc', 'PVC'),
        ('abs', 'ABS'),
    ], string='Tape Material', help='Material of the carrier tape')

    cover_tape_material = fields.Selection([
        ('pet', 'PET'),
        ('heat_activated', 'Heat Activated'),
        ('pressure_sensitive', 'Pressure Sensitive'),
    ], string='Cover Tape Material')

    cover_tape_peel_strength = fields.Float(
        string='Peel Strength (N)',
        help='Cover tape peel strength in Newtons'
    )

    def _onchange_quantity_code(self):
        for record in self:
            record.components_per_reel = record.quantity_code and int(record.quantity_code[:-1])*1000 or 0


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    @api.onchange('package_type_id')
    def _onchange_package_type_id(self):
        for record in self:
            record.qty = record.package_type_id.components_per_reel
