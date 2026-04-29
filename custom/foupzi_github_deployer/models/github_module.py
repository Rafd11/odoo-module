import json
import logging
import os
import shutil
import subprocess
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


class FoupziGithubModule(models.Model):
    _name = 'foupzi.github.module'
    _description = 'GitHub Module'
    _order = 'category, name'
    _rec_name = 'name'

    name = fields.Char('Module Name', required=True, readonly=True)
    category = fields.Char('Category', readonly=True)
    github_path = fields.Char('GitHub Path', readonly=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('deployed', 'Deployed'),
        ('installed', 'Installed'),
    ], default='available', readonly=True)
    odoo_module_id = fields.Many2one(
        'ir.module.module', string='Odoo Module', readonly=True,
        compute='_compute_odoo_module', store=False,
    )
    is_odoo_installed = fields.Boolean(
        compute='_compute_odoo_module', store=False,
    )
    deploy_log = fields.Text('Last Deploy Log', readonly=True)

    @api.depends('name')
    def _compute_odoo_module(self):
        for rec in self:
            mod = self.env['ir.module.module'].search([('name', '=', rec.name)], limit=1)
            rec.odoo_module_id = mod
            rec.is_odoo_installed = mod.state in ('installed', 'to upgrade') if mod else False

    # ------------------------------------------------------------------
    # GitHub API helpers
    # ------------------------------------------------------------------

    def _get_config(self):
        ICP = self.env['ir.config_parameter'].sudo()
        token = ICP.get_param('foupzi_github_deployer.token', '')
        owner = ICP.get_param('foupzi_github_deployer.owner', 'Rafd11')
        repo = ICP.get_param('foupzi_github_deployer.repo', 'odoo-module')
        branch = ICP.get_param('foupzi_github_deployer.branch', 'main')
        addons_path = ICP.get_param('foupzi_github_deployer.addons_path', '')
        return token, owner, repo, branch, addons_path

    def _github_request(self, url, token):
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github+json')
        req.add_header('X-GitHub-Api-Version', '2022-11-28')
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise UserError(_('GitHub API error %s: %s') % (e.code, e.reason))
        except Exception as e:
            raise UserError(_('Network error: %s') % str(e))

    # ------------------------------------------------------------------
    # Sync modules from GitHub
    # ------------------------------------------------------------------

    @api.model
    def action_sync_from_github(self):
        token, owner, repo, branch, _ = self._get_config()
        base_url = f'https://api.github.com/repos/{owner}/{repo}/contents'

        synced = 0
        for category in CATEGORIES:
            try:
                items = self._github_request(f'{base_url}/{category}?ref={branch}', token)
            except UserError:
                continue
            if not isinstance(items, list):
                continue
            for item in items:
                if item.get('type') != 'dir':
                    continue
                module_name = item['name']
                existing = self.search([('name', '=', module_name)], limit=1)
                vals = {
                    'name': module_name,
                    'category': category,
                    'github_path': item.get('path', f'{category}/{module_name}'),
                }
                if existing:
                    existing.write(vals)
                else:
                    self.create(vals)
                synced += 1

        # Mark deployed modules
        self._refresh_deploy_state()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sync complete'),
                'message': _('%d modules found in GitHub.') % synced,
                'type': 'success',
                'sticky': False,
            },
        }

    def _refresh_deploy_state(self):
        ICP = self.env['ir.config_parameter'].sudo()
        addons_path = ICP.get_param('foupzi_github_deployer.addons_path', '')
        if not addons_path:
            return
        for rec in self:
            mod_path = os.path.join(addons_path, rec.name)
            odoo_mod = self.env['ir.module.module'].search([('name', '=', rec.name)], limit=1)
            if odoo_mod and odoo_mod.state in ('installed', 'to upgrade'):
                rec.state = 'installed'
            elif os.path.isdir(mod_path):
                rec.state = 'deployed'
            else:
                rec.state = 'available'

    # ------------------------------------------------------------------
    # Deploy
    # ------------------------------------------------------------------

    def action_deploy(self):
        self.ensure_one()
        token, owner, repo, branch, addons_path = self._get_config()
        if not addons_path:
            raise UserError(_('Set the Addons Path in Settings → Technical → GitHub Module Deployer first.'))

        zip_url = f'https://api.github.com/repos/{owner}/{repo}/zipball/{branch}'
        log_lines = []

        try:
            tmp_dir = tempfile.mkdtemp(prefix='foupzi_deploy_')
            zip_path = os.path.join(tmp_dir, 'repo.zip')

            # Download repo zip
            log_lines.append(f'Downloading {zip_url} ...')
            req = urllib.request.Request(zip_url)
            if token:
                req.add_header('Authorization', f'Bearer {token}')
            req.add_header('Accept', 'application/vnd.github+json')
            with urllib.request.urlopen(req, timeout=60) as resp:
                with open(zip_path, 'wb') as f:
                    f.write(resp.read())
            log_lines.append('Download OK.')

            # Extract
            extract_dir = os.path.join(tmp_dir, 'extract')
            os.makedirs(extract_dir)
            with ZipFile(zip_path, 'r') as z:
                z.extractall(extract_dir)

            # Find module inside extracted zip (structure: owner-repo-SHA/category/module_name/)
            module_src = None
            for root, dirs, _ in os.walk(extract_dir):
                for d in dirs:
                    if d == self.name:
                        candidate = os.path.join(root, d)
                        if os.path.exists(os.path.join(candidate, '__manifest__.py')):
                            module_src = candidate
                            break
                if module_src:
                    break

            if not module_src:
                raise UserError(_('Module "%s" not found in the repository zip.') % self.name)

            log_lines.append(f'Found module at: {module_src}')

            # Copy to addons path
            dest = os.path.join(addons_path, self.name)
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(module_src, dest)
            log_lines.append(f'Deployed to: {dest}')

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        # Update Odoo module list
        self.env['ir.module.module'].sudo().update_list()
        log_lines.append('Odoo module list updated.')

        self.write({
            'state': 'deployed',
            'deploy_log': '\n'.join(log_lines),
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Deployed'),
                'message': _('Module "%s" deployed to %s') % (self.name, addons_path),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_deploy_and_install(self):
        self.ensure_one()
        self.action_deploy()
        mod = self.env['ir.module.module'].search([('name', '=', self.name)], limit=1)
        if not mod:
            raise UserError(_('Module "%s" not found after deploy. Check the addons path is in odoo.conf.') % self.name)
        if mod.state == 'uninstalled':
            mod.button_immediate_install()
        elif mod.state in ('installed', 'to upgrade'):
            mod.button_immediate_upgrade()
        self.state = 'installed'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Installed'),
                'message': _('Module "%s" installed successfully.') % self.name,
                'type': 'success',
                'sticky': False,
            },
        }

    def action_upgrade(self):
        self.ensure_one()
        mod = self.env['ir.module.module'].search([('name', '=', self.name)], limit=1)
        if not mod or mod.state not in ('installed', 'to upgrade'):
            raise UserError(_('Module is not installed yet. Use Deploy & Install first.'))
        self.action_deploy()
        mod.button_immediate_upgrade()
        self.state = 'installed'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Upgraded'),
                'message': _('Module "%s" upgraded successfully.') % self.name,
                'type': 'success',
                'sticky': False,
            },
        }

    # ------------------------------------------------------------------
    # Shell command runner (for advanced ops on the server)
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
