import subprocess

from odoo import _, fields, models
from odoo.exceptions import UserError

ALLOWED_COMMANDS = (
    'git', 'ls', 'pwd', 'odoo', 'python3', 'pip3', 'pip',
    'systemctl', 'service', 'odoo-bin',
)


class FoupziShellWizard(models.TransientModel):
    _name = 'foupzi.shell.wizard'
    _description = 'Run Server Command'

    command = fields.Char('Command', required=True)
    output = fields.Text('Output', readonly=True)
    working_dir = fields.Char('Working Directory', default='/opt/odoo')

    def action_run(self):
        self.ensure_one()
        cmd = self.command.strip()
        if not cmd:
            raise UserError(_('Enter a command.'))

        # Basic safety: only allow whitelisted base commands
        base_cmd = cmd.split()[0].split('/')[-1]
        if base_cmd not in ALLOWED_COMMANDS:
            raise UserError(
                _('Command "%s" is not allowed. Allowed: %s')
                % (base_cmd, ', '.join(ALLOWED_COMMANDS))
            )

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.working_dir or '/tmp',
            )
            output = result.stdout or ''
            if result.stderr:
                output += '\n--- stderr ---\n' + result.stderr
            self.output = output or '(no output)'
        except subprocess.TimeoutExpired:
            self.output = 'Command timed out after 60 seconds.'
        except Exception as e:
            self.output = f'Error: {e}'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'foupzi.shell.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
