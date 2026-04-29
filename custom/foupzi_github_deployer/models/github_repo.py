from odoo import _, fields, models


class FoupziGithubRepo(models.Model):
    _name = 'foupzi.github.repo'
    _description = 'GitHub Repository'
    _order = 'sequence, name'

    name = fields.Char('Label', required=True)
    owner = fields.Char('Owner', required=True)
    repo_name = fields.Char('Repository', required=True)
    branch = fields.Char('Branch', default='main')
    token = fields.Char('GitHub Token (optional override)',
                        help='Leave blank to use the global token from Settings.')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    module_ids = fields.One2many('foupzi.github.module', 'repo_id', string='Modules')
    module_count = fields.Integer(compute='_compute_module_count', store=True)

    def _compute_module_count(self):
        for r in self:
            r.module_count = len(r.module_ids)

    def action_sync(self):
        """Sync this repo and open marketplace filtered to it."""
        self.ensure_one()
        count = self.env['foupzi.github.module']._sync_repo(self)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Modules — %s') % self.name,
            'res_model': 'foupzi.github.module',
            'view_mode': 'kanban,list',
            'domain': [('repo_id', '=', self.id)],
            'context': {'search_default_group_category': 1},
            'target': 'current',
        }

    def action_view_modules(self):
        """Open marketplace filtered to this repo."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Modules — %s') % self.name,
            'res_model': 'foupzi.github.module',
            'view_mode': 'kanban,list',
            'domain': [('repo_id', '=', self.id)],
            'context': {'search_default_group_category': 1},
            'target': 'current',
        }
