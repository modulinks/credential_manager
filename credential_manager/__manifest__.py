{
    'name': 'Credential Manager',
    'version': '17.0.1.0.0',
    'category': 'Administration',
    'summary': 'Simplified Bitwarden-style Credential Manager for Odoo 17',
    'description': """
        <p>This module allows users to manage credentials in a centralized and secure manner.</p>
        <p>Ideal for teams needing to share access without compromising security.</p>
        <ul>
            <li>User-friendly interface to manage credentials</li>
            <li>Permission control per user</li>
            <li>Compatible with Odoo 17 Enterprise and Community</li>
        </ul>
    """,
    'author': 'Modulink',
    'depends': ['base', 'web', 'mail'],
    'external_dependencies': {
        'python': ['pyotp', 'lxml'],
    },
    'data': [
        'security/credential_manager_security.xml',
        'security/ir.model.access.csv',
        'views/credential_views.xml',
        'views/password_history_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'credential_manager/static/src/js/credential_copy.js',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/icon.png'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 69.99,
    'currency': 'USD',
}