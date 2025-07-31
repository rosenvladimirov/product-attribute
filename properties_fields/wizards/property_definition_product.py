from odoo import models, fields, api


class PropertyDefinitionFixWizard(models.TransientModel):
    _name = 'property.definition.fix.wizard'
    _description = 'Property Definition Fix Wizard'

    property_definition_id = fields.PropertiesDefinition(
        string='Property Definition',
    )

    def action_apply(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])

        if not active_ids:
            return {'type': 'ir.actions.act_window_close'}

        products = self.env['product.template'].browse(active_ids)
        for product in products:
            if hasattr(product, 'properties'):
                product.properties.update({
                    'definition_id': self.property_definition_id,
                })

        return {'type': 'ir.actions.act_window_close'}
