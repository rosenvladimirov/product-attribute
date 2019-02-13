# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
#from odoo.addons.muk_dms_field.fields import dms_fields

import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.template"

    homologation = fields.Char('Homologation', help="Plase fill the Homologation code")
    show_homologation = fields.Boolean('Show in documents')
    #homologation_document = dms_fields.DocumentBinary(string="File", filename=_get_filename, directory=_get_directory)
