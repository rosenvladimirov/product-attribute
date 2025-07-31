# Copyright 2025 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Properties Fields',
    'summary': """Add support for link fields from currect model in product properties fields.""",
    'version': '18.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov,Odoo Community Association (OCA)',
    'depends': [
        'base',
        'web',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv'
    ],
    'demo': [
    ],
    'assets': {
        'web.assets_backend': [
            # Първо зареждате вашите компоненти
            'properties_fields/static/src/views/fields/properties/extended_properties_field.js',
            'properties_fields/static/src/views/fields/properties/extended_properties_fields.xml',
            'properties_fields/static/src/views/fields/properties/extended_properties_field.scss',

            # След това патч файловете
            'properties_fields/static/src/views/fields/properties/extended_property_definition.js',
            'properties_fields/static/src/views/fields/properties/extended_property_definition.xml',
            'properties_fields/static/src/views/fields/properties/extended_property_definition.scss',

            'properties_fields/static/src/views/fields/properties/extended_property_value.js',
            'properties_fields/static/src/views/fields/properties/extended_property_value.xml',

            'properties_fields/static/src/views/fields/properties/properties_definition_viewer.js',
            'properties_fields/static/src/views/fields/properties/properties_definition_viewer.xml',
            'properties_fields/static/src/views/fields/properties/properties_definition_viewer.scss',
        ],
    },
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
    'application': False,
}
