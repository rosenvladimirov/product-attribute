# coding: utf-8

from odoo import api, fields, models, tools, _
from odoo.addons.base.res.res_partner import Partner as ResPartner
from odoo.osv.expression import get_unaccent_wrapper

import logging
_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = 'res.partner'

    customs_agent_id = fields.Many2one('res.users', string='Customs agent',
                help='The internal user that is in charge of communicating with Customs agence if any.')
