import base64
import os
import shutil
import tempfile

from odoo import _, fields, models
from odoo.exceptions import UserError


class FoupziZipUpload(models.TransientModel):
    _name = 'foupzi.zip.upload'
    _description = 'Upload Module ZIP'

    zip_file = fields.Binary('ZIP File', required=True)
    zip_filename = fields.Char('Filename')
    module_name = fields.Char(
        'Module Name',
        help='Technical name of the module (folder name). Leave blank to auto-detect from the ZIP.',
    )
    result = fields.Text('Result', readonly=True)

    def action_upload(self):
        self.ensure_one()
        addons_path = self.env['ir.config_parameter'].sudo().get_param(
            'foupzi_github_deployer.addons_path', ''
        )
        if not addons_path:
            raise UserError(_('Set the Addons Path in Settings → GitHub Module Deployer first.'))
        if not os.path.isdir(addons_path):
            raise UserError(_('Addons path "%s" does not exist on this server.') % addons_path)

        zip_data = base64.b64decode(self.zip_file)
        tmp = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        try:
            tmp.write(zip_data)
            tmp.close()
            module_name = self._install_zip(tmp.name, addons_path)
        finally:
            os.unlink(tmp.name)

        # refresh module list
        self.env['ir.module.module'].sudo().update_list()
        self.result = f'Module "{module_name}" deployed to {addons_path}.\nRefresh Apps to install it.'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'foupzi.zip.upload',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _install_zip(self, zip_path, addons_path):
        from zipfile import ZipFile, BadZipFile
        try:
            zf = ZipFile(zip_path, 'r')
        except BadZipFile:
            raise UserError(_('The uploaded file is not a valid ZIP archive.'))

        extract_dir = tempfile.mkdtemp(prefix='foupzi_upload_')
        try:
            zf.extractall(extract_dir)
            zf.close()

            module_name = self.module_name.strip() if self.module_name else ''
            module_src = self._find_module_dir(extract_dir, module_name)

            if not module_src:
                raise UserError(
                    _('Could not find a valid Odoo module (missing __manifest__.py) in the ZIP.\n'
                      'Tip: specify the module name manually.')
                )

            module_name = os.path.basename(module_src)
            dest = os.path.join(addons_path, module_name)
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(module_src, dest)
            return module_name
        finally:
            shutil.rmtree(extract_dir, ignore_errors=True)

    def _find_module_dir(self, root, hint_name):
        """Walk root and return the first directory containing __manifest__.py.
        If hint_name is given, prefer a dir with that name."""
        best = None
        for dirpath, dirs, files in os.walk(root):
            if '__manifest__.py' in files:
                if hint_name and os.path.basename(dirpath) == hint_name:
                    return dirpath
                if best is None:
                    best = dirpath
        return best
