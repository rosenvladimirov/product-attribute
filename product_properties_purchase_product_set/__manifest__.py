# Copyright 2023-2025 Rosen Vladimirov, BioPrint Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Product Properties Sale Product Set',
    'summary': 'Add support of product properties in sale order product sets',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, BioPrint Ltd., Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/sale-workflow',
    'maintainers': ['rosenvladimirov'],
    'development_status': 'Beta',
    'depends': [
        'purchase_product_set',
        'product_properties',
        'product_properties_product_set',
        'purchase_layout_category_hide_detail'
    ],
    'data': [
        'report/report_purchaseorder_templates.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
