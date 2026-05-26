# Copyright 2023-2025 Rosen Vladimirov, BioPrint Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Product Properties Invoice Product Set',
    'summary': 'Add switching between printing modes for invoice product sets',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, BioPrint Ltd., Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-invoicing',
    'maintainers': ['rosenvladimirov'],
    'development_status': 'Beta',
    'depends': [
        'account_invoice_product_set',
        'product_properties_product_set',
        'sale_layout_category_hide_detail',
    ],
    'data': [
        'report/report_invoice.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
