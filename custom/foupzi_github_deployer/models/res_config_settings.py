from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    github_token = fields.Char(
        string='GitHub Token',
        config_parameter='foupzi_github_deployer.token',
    )
    github_owner = fields.Char(
        string='Repository Owner',
        config_parameter='foupzi_github_deployer.owner',
        default='Rafd11',
    )
    github_repo = fields.Char(
        string='Repository Name',
        config_parameter='foupzi_github_deployer.repo',
        default='odoo-module',
    )
    github_branch = fields.Char(
        string='Branch',
        config_parameter='foupzi_github_deployer.branch',
        default='main',
    )
    github_addons_path = fields.Char(
        string='Addons Path on Server',
        config_parameter='foupzi_github_deployer.addons_path',
        help='Absolute path where modules will be deployed, e.g. /opt/odoo/addons',
    )
