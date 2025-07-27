{
    'name': 'Gestor de Credenciales',
    'version': '1.0',
    'category': 'Administration',
    'summary': 'Gestor de credenciales simplificado al estilo Bitwarden para Odoo 16',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/credential_manager_security.xml',
        'security/ir.model.access.csv',
        'views/credential_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'price': 159.99,
    'currency': 'USD',

}