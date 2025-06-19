# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
from odoo.addons.product_electrical_properties.models.product_template import MOISTURE_LEVELS, STORAGE_CONDITIONS
_logger = logging.getLogger(__name__)

NEXAR_PART_ATTRIBUTES = """
query specAttributes(
    $mpn: String!
    $limit: Int
){
  supSearchMpn(
    q: $mpn
    limit: $limit
    ) {
    hits
    results {
      part {
        id
        name
        mpn
        specs {
          attribute {
            name
            id
            shortname
          }
          displayValue
        }
      }
    }
  }
}
"""
NEXAR_ALTERNATIVE_PART = """query findAlternativeParts(
    $mpn: String!
    $limit: Int
) {
  supSearchMpn(
    q: $mpn
    limit: $limit
    ) {
    hits
    results {
      part {
        similarParts {
          name
          octopartUrl
          mpn
        }
      }
    }
  }
}"""


class ProductProduct(models.Model):
    _inherit = "product.product"

    component_type_id = fields.Many2one(
        'component.definition.properties',
        'Definition properties',
    )
    # component_properties = fields.Properties(
    #     'Component technical data',
    #     definition='component_properties_definition'
    # )
    component_properties = fields.Properties(
        'Component technical data',
        definition='component_type_id.component_properties_definition'
    )
    moisture_sensitivity_level = fields.Selection(
        MOISTURE_LEVELS,
        string='MSL'
    )

    esd_protection = fields.Boolean(
        string='ESD Protection',
        help='Indicates if the packaging has ESD protection'
    )

    storage_conditions = fields.Selection(
        STORAGE_CONDITIONS,
        string='Storage Conditions'
    )

    def _update_template_properties(self, template, values):
        """Helper method to update template properties when variant properties change."""
        if template.product_variant_count == 1 and 'product_tmpl_id' not in values:
            template_values = {}
            if 'component_properties' in values:
                template_values['component_properties'] = values['component_properties']
            if 'component_type_id' in values:
                template_values.update({
                    'component_type_id': values['component_type_id'],
                })
            if template_values:
                template.with_context(**dict(self._context, block_properties=True)).write(template_values)

    @api.model_create_multi
    def create(self, vals_list):
        """Create product variants with proper property handling."""
        records = super().create(vals_list)

        if not self._context.get('block_properties'):
            for record, vals in zip(records, vals_list):
                self._update_template_properties(record.product_tmpl_id, vals)
        return records

    def write(self, vals):
        """Update product variants with proper property handling."""
        if not self._context.get('block_properties'):
            templates = self.mapped('product_tmpl_id')
            for template in templates:
                self._update_template_properties(template, vals)
        return super().write(vals)

    def _get_product_properties(self, key, value):
        """Extract properties for a given key-value pair."""
        all_properties = self.read(['component_properties'])[0]['component_properties']
        return {
            prop['name']: value
            for prop in all_properties
            if prop['string'] == key
        }

    def action_update_nexar_data(self):
        """Update product properties from Nexar API data."""
        for record in self:
            all_properties = self.read(['component_properties'])[0]['component_properties']
            mpn_properties = [prop for prop in all_properties if prop['string'] == 'mpn']

            current_properties = record.component_properties or {}

            for mpn_prop in mpn_properties:
                if not mpn_prop.get('value'):
                    continue

                status, response, _ = self.env.user._do_request('', json={
                    "query": NEXAR_PART_ATTRIBUTES,
                    "variables": {
                        'mpn': mpn_prop['value'],
                        'limit': 1
                    }
                })

                if not response.get('data'):
                    _logger.info(f"Status: {status}")
                    continue

                for result in response['data'].get('supSearchMpn', {}).get('results', []):
                    for part in result.get('part', {}).get('specs', []):
                        attr_name = part.get('attribute', {}).get('name')
                        if attr_name == 'mpm':
                            continue
                        current_properties.update(
                            record._get_product_properties(attr_name, part.get('displayValue'))
                        )

            record.component_properties = current_properties
