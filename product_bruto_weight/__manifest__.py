{
    'name': 'Product Bruto Weight Calculation',
    'version': '12.0.1.0.0',
    'author': 'Rosen Vladimirov, dXFactory Ltd.',
    'website': 'https://github.com/rosenvladimirov/product-attribute',
    'license': 'AGPL-3',
    'category': 'Warehouse',
    'summary': 'Allows to calculate products bruto weight from its components.',
    'depends': [
        'mrp',
    ],
    'data': [
        'wizard/product_bruto_weight_update_view.xml',
        'views/product_view.xml',
    ],
    'installable': True,
}
