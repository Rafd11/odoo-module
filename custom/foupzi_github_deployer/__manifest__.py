{
    'name': 'GitHub Module Deployer',
    'version': '19.0.1.0.0',
    'summary': 'Browse and deploy Odoo modules directly from GitHub',
    'description': 'Browse your GitHub repository, install and update Odoo modules with one click.',
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
