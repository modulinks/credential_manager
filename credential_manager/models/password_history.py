from odoo import models, fields, api
from datetime import datetime

class CredentialPasswordHistory(models.Model):
    _name = 'credential.password.history'
    _description = 'Password History'
    _order = 'change_date desc'

    credential_id = fields.Many2one('credential.manager', string='Credential', required=True, ondelete='cascade')
    old_password = fields.Char(string='Previous Password')
    old_ssh_password = fields.Char(string='Previous SSH Password')
    old_ssh_root_password = fields.Char(string='Previous SSH Root Password')
    change_date = fields.Datetime(string='Change Date', default=fields.Datetime.now, required=True)
    changed_by = fields.Many2one('res.users', string='Changed By', default=lambda self: self.env.user, required=True)
    change_type = fields.Selection([
        ('password', 'Login Password'),
        ('ssh_password', 'SSH Password'),
        ('ssh_root_password', 'SSH Root Password'),
        ('multiple', 'Multiple Passwords')
    ], string='Change Type', required=True)

class PasswordHistoryWizard(models.TransientModel):
    _name = 'password.history.wizard'
    _description = 'Password History Wizard'

    credential_id = fields.Many2one('credential.manager', string='Credential', required=True)
    history_ids = fields.One2many('password.history.wizard.line', 'wizard_id', string='Password History')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        credential_id = self._context.get('active_id')
        if credential_id:
            res['credential_id'] = credential_id
            # Cargar el historial
            history_records = self.env['credential.password.history'].search([
                ('credential_id', '=', credential_id)
            ], order='change_date desc')
            
            history_lines = []
            for record in history_records:
                line_data = {
                    'change_date': record.change_date,
                    'changed_by': record.changed_by.name,
                    'change_type': record.change_type,
                }
                
                # Solo mostrar las contraseñas que cambiaron
                passwords_shown = []
                if record.change_type == 'password' and record.old_password:
                    passwords_shown.append(f"Login: {record.old_password}")
                elif record.change_type == 'ssh_password' and record.old_ssh_password:
                    passwords_shown.append(f"SSH: {record.old_ssh_password}")
                elif record.change_type == 'ssh_root_password' and record.old_ssh_root_password:
                    passwords_shown.append(f"SSH Root: {record.old_ssh_root_password}")
                elif record.change_type == 'multiple':
                    if record.old_password:
                        passwords_shown.append(f"Login: {record.old_password}")
                    if record.old_ssh_password:
                        passwords_shown.append(f"SSH: {record.old_ssh_password}")
                    if record.old_ssh_root_password:
                        passwords_shown.append(f"SSH Root: {record.old_ssh_root_password}")
                
                line_data['passwords_display'] = " | ".join(passwords_shown)
                history_lines.append((0, 0, line_data))
            
            res['history_ids'] = history_lines
        return res

class PasswordHistoryWizardLine(models.TransientModel):
    _name = 'password.history.wizard.line'
    _description = 'Password History Line'

    wizard_id = fields.Many2one('password.history.wizard', string='Wizard')
    change_date = fields.Datetime(string='Date')
    changed_by = fields.Char(string='Changed By')
    change_type = fields.Selection([
        ('password', 'Login Password'),
        ('ssh_password', 'SSH Password'),
        ('ssh_root_password', 'SSH Root Password'),
        ('multiple', 'Multiple Passwords')
    ], string='Type')
    passwords_display = fields.Char(string='Previous Passwords')