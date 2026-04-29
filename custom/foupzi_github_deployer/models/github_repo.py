from odoo import fields, models


class FoupziGithubRepo(models.Model):
    _name = 'foupzi.github.repo'
    _description = 'GitHub Repository'
    _order = 'sequence, name'

    name = fields.Char('Label', required=True)
    owner = fields.Char('Owner', required=True)
    repo_name = fields.Char('Repository', required=True)
    branch = fields.Char('Branch', default='main')
    token = fields.Char('GitHub Token (optional override)', help='Leave blank to use the token from Settings.')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    module_ids = fields.One2many('foupzi.github.module', 'repo_id', string='Modules')
    module_count = fields.Integer(compute='_compute_module_count')

    def _compute_module_count(self):
        for r in self:
            r.module_count = len(r.module_ids)
