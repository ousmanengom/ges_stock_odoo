{
    'name': "stock inherit",
    'version': '1.0',
    'depends': ['base','stock'],
    'author': "Nassif,Ousmane, WELE,AIBD",
    'category': 'STOCK',
    'description': """
    Gestion stock
    """,
    'sequence': -1000,
    'data': [
        'views/product_template_views.xml',
        'security/ir.model.access.csv',

    ],
    'installable':True,
    'application':True,
    'auto_install':False,
}