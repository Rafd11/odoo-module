{
    'name': 'Module Marketplace',
    'version': '19.0.2.0.0',
    'summary': 'Browse, install and upload Odoo modules from GitHub or ZIP files',
    'category': 'Technical',
    'author': 'Rafd11',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/github_module_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
