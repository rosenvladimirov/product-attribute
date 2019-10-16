{
    'name': 'Product External default code',
    'category': 'Sales',
    "author" : "Rosen Vladimirov, dXFactory Ltd.",
    'summary': 'Add product External default code',
    'version': '12.0.1.0',
    'description': "This module add extra field for external default code in template or variants.",
    'depends': ['product'],
    'data': [
        'views/product_template_views.xml',
        'views/product_views.xml',
        #'views/report_invoice.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
}
