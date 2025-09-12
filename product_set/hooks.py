#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    product_tmpl_id = env['product.template'].create({
        'name': 'Manuals & Instructions for using',
        'detailed_type': 'product',
        'sale_ok': True,
        'purchase_ok': True,
        'default_code': 'IFU',
        'categ_id': env.ref('product_set.product_category_compensation_product').id
    })
    res_id = product_tmpl_id.product_variant_ids[0].id
    _logger.info("Crete product template [%s] %s"
                 % (res_id, product_tmpl_id.display_name))
    env['ir.model.data'].create({
        "module": "product_set",
        "name": 'compensation_product',
        "model": 'product.product',
        "noupdate": True,
        "res_id": res_id,
        "reference": f"product.product,{res_id}"
    })
