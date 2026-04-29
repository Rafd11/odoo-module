import json
import logging
import os
import shutil
import tempfile
import urllib.request
import urllib.error
from zipfile import ZipFile

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

CATEGORIES = [
    'accounting', 'hr', 'pos', 'website',
    'helpdesk', 'inventory', 'integrations', 'security', 'custom',
]

CATEGORY_ICONS = {
    'accounting': 'fa-calculator',
    'hr': 'fa-users',
    'pos': 'fa-shopping-cart',
    'website': 'fa-globe',
    'helpdesk': 'fa-life-ring',
    'inventory': 'fa-cubes',
    'integrations': 'fa-plug',
    'security': 'fa-shield',
    'custom': 'fa-wrench',
}


class FoupziGithubModule(models.Model):
    _name = 'foupzi.github.module'
    _description = 'GitHub Module'
    _order = 'category, name'

    name = fields.Char('Module Name', required=True, readonly=True)
    display_name_custom = fields.Char('Display Name', compute='_compute_display_name_custom', store=False)
    category = fields.Char('Category', readonly=True)
    category_icon = fields.Char('Category Icon', compute='_compute_category_icon', store=False)
    github_path = fields.Char('GitHub Path', readonly=True)
    repo_id = fields.Many2one('foupzi.github.repo', string='Repository', readonly=True, ondelete='cascade')
    repo_label = fields.Char(related='repo_id.name', string='Repo', store=False)
    state = fields.Selection([
        ('available', 'Available'),
        ('deployed', 'Deployed'),
        ('installed', 'Installed'),
    ], default='available', readonly=True)
    is_odoo_installed = fields.Boolean(compute='_compute_odoo_state', store=False)
    deploy_log = fields.Text('Last Deploy Log', readonly=True)

    @api.depends('name')
    def _compute_display_name_custom(self):
        for rec in self:
            rec.display_name_custom = rec.name.replace('_', ' ').title()

    @api.depends('category')
    def _compute_category_icon(self):
        for rec in self:
            rec.category_icon = CATEGORY_ICONS.get(rec.category, 'fa-puzzle-piece')

    @api.depends('name')
    def _compute_odoo_state(self):
        for rec in self:
            mod = self.env['ir.module.module'].search([('name', '=', rec.name)], limit=1)
            rec.is_odoo_installed = mod.state in ('installed', 'to upgrade') if mod else False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_global_config(self):
        ICP = self.env['ir.config_parameter'].sudo()
        return {
            'token': ICP.get_param('foupzi_github_deployer.token', ''),
            'addons_path': ICP.get_param('foupzi_github_deployer.addons_path', ''),
        }

    def _get_repo_config(self):
        """Return (owner, repo_name, branch, token) for this module's repo."""
        self.ensure_one()
        cfg = self._get_global_config()
        if self.repo_id:
            return (
                self.repo_id.owner,
                self.repo_id.repo_name,
                self.repo_id.branch or 'main',
                self.repo_id.token or cfg['token'],
            )
        # fallback to global settings
        ICP = self.env['ir.config_parameter'].sudo()
        return (
            ICP.get_param('foupzi_github_deployer.owner', 'Rafd11'),
            ICP.get_param('foupzi_github_deployer.repo', 'odoo-module'),
            ICP.get_param('foupzi_github_deployer.branch', 'main'),
            cfg['token'],
        )

    def _github_get(self, url, token):
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github+json')
        req.add_header('X-GitHub-Api-Version', '2022-11-28')
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise UserError(_('GitHub API error %s: %s') % (e.code, e.reason))
        except Exception as e:
            raise UserError(_('Network error: %s') % str(e))

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    @api.model
    def action_sync_all_repos(self):
        """Sync modules from all active repos."""
        repos = self.env['foupzi.github.repo'].search([('active', '=', True)])
        if not repos:
            # fallback: sync from global config as before
            return self._sync_repo(None)
        total = 0
        for repo in repos:
            total += self._sync_repo(repo)
        return self._notify(_('%d modules synced from %d repos.') % (total, len(repos)))

    def _sync_repo(self, repo):
        ICP = self.env['ir.config_parameter'].sudo()
        if repo:
            owner, repo_name, branch, token = (
                repo.owner, repo.repo_name, repo.branch or 'main',
                repo.token or ICP.get_param('foupzi_github_deployer.token', '')
            )
        else:
            owner = ICP.get_param('foupzi_github_deployer.owner', 'Rafd11')
            repo_name = ICP.get_param('foupzi_github_deployer.repo', 'odoo-module')
            branch = ICP.get_param('foupzi_github_deployer.branch', 'main')
            token = ICP.get_param('foupzi_github_deployer.token', '')

        base_url = f'https://api.github.com/repos/{owner}/{repo_name}/contents'
        synced = 0

        for category in CATEGORIES:
            try:
                items = self._github_get(f'{base_url}/{category}?ref={branch}', token)
            except UserError:
                continue
            if not isinstance(items, list):
                continue
            for item in items:
                if item.get('type') != 'dir':
                    continue
                module_name = item['name']
                domain = [('name', '=', module_name)]
                if repo:
                    domain.append(('repo_id', '=', repo.id))
                existing = self.search(domain, limit=1)
                vals = {
                    'name': module_name,
                    'category': category,
                    'github_path': item.get('path', f'{category}/{module_name}'),
                    'repo_id': repo.id if repo else False,
                }
                if existing:
                    existing.write(vals)
                else:
                    self.create(vals)
                synced += 1

        self._refresh_deploy_states()
        return synced

    def _refresh_deploy_states(self):
        addons_path = self.env['ir.config_parameter'].sudo().get_param(
            'foupzi_github_deployer.addons_path', ''
        )
        for rec in self:
            mod = self.env['ir.module.module'].search([('name', '=', rec.name)], limit=1)
            if mod and mod.state in ('installed', 'to upgrade'):
                rec.state = 'installed'
            elif addons_path and os.path.isdir(os.path.join(addons_path, rec.name)):
                rec.state = 'deployed'
            else:
                rec.state = 'available'

    # ------------------------------------------------------------------
    # Deploy
    # ------------------------------------------------------------------

    def _deploy_zip_to_addons(self, zip_path, module_name, addons_path):
        """Extract module_name from zip_path into addons_path. Returns deploy log."""
        log = []
        extract_dir = tempfile.mkdtemp(prefix='foupzi_ext_')
        try:
            with ZipFile(zip_path, 'r') as z:
                z.extractall(extract_dir)

            module_src = None
            for root, dirs, _ in os.walk(extract_dir):
                for d in dirs:
                    if d == module_name:
                        candidate = os.path.join(root, d)
                        if os.path.exists(os.path.join(candidate, '__manifest__.py')):
                            module_src = candidate
                            break
                if module_src:
                    break

            if not module_src:
                # maybe the zip IS the module (no subfolder)
                if os.path.exists(os.path.join(extract_dir, '__manifest__.py')):
                    module_src = extract_dir
                else:
                    raise UserError(_('Module "%s" not found in zip.') % module_name)

            dest = os.path.join(addons_path, module_name)
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(module_src, dest)
            log.append(f'Deployed to: {dest}')
        finally:
            if extract_dir != module_src:
                shutil.rmtree(extract_dir, ignore_errors=True)
        return log

    def action_deploy(self):
        self.ensure_one()
        addons_path = self._get_global_config()['addons_path']
        if not addons_path:
            raise UserError(_('Set the Addons Path in Settings → GitHub Module Deployer first.'))

        owner, repo_name, branch, token = self._get_repo_config()
        zip_url = f'https://api.github.com/repos/{owner}/{repo_name}/zipball/{branch}'
        log = [f'Downloading from {owner}/{repo_name}@{branch} ...']

        tmp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        try:
            req = urllib.request.Request(zip_url)
            if token:
                req.add_header('Authorization', f'Bearer {token}')
            req.add_header('Accept', 'application/vnd.github+json')
            with urllib.request.urlopen(req, timeout=60) as resp:
                tmp_zip.write(resp.read())
            tmp_zip.close()
            log.append('Download complete.')
            log += self._deploy_zip_to_addons(tmp_zip.name, self.name, addons_path)
        finally:
            tmp_zip.close()
            os.unlink(tmp_zip.name)

        self.env['ir.module.module'].sudo().update_list()
        log.append('Module list updated.')
        self.write({'state': 'deployed', 'deploy_log': '\n'.join(log)})
        return self._notify(_('"%s" deployed successfully.') % self.name, 'success')

    def action_deploy_and_install(self):
        self.ensure_one()
        self.action_deploy()
        mod = self.env['ir.module.module'].search([('name', '=', self.name)], limit=1)
        if not mod:
            raise UserError(_('Module "%s" not found after deploy. Ensure the addons path is in odoo.conf.') % self.name)
        if mod.state == 'uninstalled':
            mod.button_immediate_install()
        elif mod.state in ('installed', 'to upgrade'):
            mod.button_immediate_upgrade()
        self.state = 'installed'
        return self._notify(_('"%s" installed.') % self.name, 'success')

    def action_upgrade(self):
        self.ensure_one()
        mod = self.env['ir.module.module'].search([('name', '=', self.name)], limit=1)
        if not mod or mod.state not in ('installed', 'to upgrade'):
            raise UserError(_('Install the module first.'))
        self.action_deploy()
        mod.button_immediate_upgrade()
        self.state = 'installed'
        return self._notify(_('"%s" upgraded.') % self.name, 'success')

    # ------------------------------------------------------------------
    # Shell runner
    # ------------------------------------------------------------------

    @api.model
    def action_open_shell(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Run Server Command'),
            'res_model': 'foupzi.shell.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.model
    def action_open_zip_upload(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Upload Module ZIP'),
            'res_model': 'foupzi.zip.upload',
            'view_mode': 'form',
            'target': 'new',
        }

    def _notify(self, msg, kind='success'):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'message': msg, 'type': kind, 'sticky': False},
        }
