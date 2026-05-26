# Copyright 2023-2025 Rosen Vladimirov, BioPrint Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Product Properties Stock Product Set',
    'summary': 'Integration between product sets and delivery slip reports',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, BioPrint Ltd., Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/stock-logistics-workflow',
    'maintainers': ['rosenvladimirov'],
    'development_status': 'Beta',
    'depends': [
        'product_properties_product_set',
        'stock_picking_product_set',
        'l10n_bg_report_stock',
        'picking_layout_category_hide_detail',  # Закоментирана зависимост
    ],
    'data': [
        'report/report_accepted_deliveryslip.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
