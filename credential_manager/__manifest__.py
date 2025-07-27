{
    'name': 'Gestor de Credenciales',
    'version': '1.0',
    'category': 'Administration',
    'summary': 'Gestor de credenciales simplificado al estilo Bitwarden para Odoo 16',
    'description': """
        <p>Este módulo permite a los usuarios gestionar credenciales de forma centralizada y segura.</p>
        <p>Ideal para equipos que necesitan compartir accesos sin comprometer la seguridad.</p>
        <ul>
            <li>Interfaz amigable para administrar credenciales</li>
            <li>Control de permisos por usuario</li>
            <li>Compatible con Odoo 16 Enterprise y Community</li>
        </ul>
    """,
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/credential_manager_security.xml',
        'security/ir.model.access.csv',
        'views/credential_views.xml',
        'views/menu.xml',
    ],
    'images': [
    'static/description/banner.png',
    'static/description/icon.png'
    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'price': 159.99,
    'currency': 'USD',
}