{
    'name': 'HR Stock Request',
    'version': '1.0',
    'depends': ['hr', 'stock'],
    'author': 'Votre Nom',
    'category': 'Human Resources',
    'summary': 'Module de gestion des demandes de matériel',
    'description': """
        Ce module permet aux employés de faire des demandes de matériel avec un processus de validation
        et une intégration avec le module de stock pour la gestion des transferts.
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/hr_stock_request_views.xml',
        'views/hr_stock_request_menus.xml',
        'data/ir_sequence_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}