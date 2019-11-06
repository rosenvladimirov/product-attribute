# -*- coding: utf-8 -*-
# © 2017 Tobias Zehntner
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name' : 'Product Dimensions',
    'category' : 'Website',
    'summary': 'Add dimensions to product template and variant',
    'description' : """
Define product dimensions on product template, variant and packaging
Product Form View > Inventory tab
- Length, width, height, weight and volume for product
- The volume is calculated automatically
- The weight can be displayed in Kilogram or Gram

Additionally, informational imperial measures can be shown aside the metric 
measures:
Sales > Configuration > Settings > Products > Show Imperial Product Measures

Behaviour between product template and variant, if dimensions are changed:
- If one of length, width, height gets changed, all three will be synced
If only one variant:
- Dimensions are set on the other when one of them is changed
If several variants:
- If template dimensions are changed, they will also be set on variants that
have none defined
- If template dimensions are changed that were previously the same on variant,
the new value will also be set on the variant
- Changing variant dimensions has no effect on template and other variants

Packaging dimensions are independent from product template/variant dimensions.
 """,
    'version' : '12.0.1.0.0',
    'license': 'AGPL-3',
    'author' : 'Niboo',
    'website': 'https://www.niboo.be',
    'depends' : [
        'delivery',
    ],
    'data': [
        'data/product_data.xml',
        'views/product_views.xml',
        #'views/res_config_settings.xml',
    ],
    'installable': True,
    'application': False,
}
