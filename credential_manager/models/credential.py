from odoo import models, fields, api
import pyotp
from odoo.exceptions import UserError

class CredentialCustomField(models.Model):
    _name = 'credential.custom.field'
    _description = 'Custom Credential Field'

    credential_id = fields.Many2one('credential.manager', string='Credential', ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    value = fields.Char(string='Value')
    field_type = fields.Selection([
        ('text', 'Text'),
        ('hidden', 'Hidden'),
        ('boolean', 'Boolean'),
        ('linked', 'Linked')
    ], string='Type', default='text', required=True)
    is_hidden = fields.Boolean(compute='_compute_is_hidden', store=False)
    linked_field = fields.Selection([
        ('user', 'User'),
        ('password', 'Password')
    ], string='Linked Field', required=False)

    @api.depends('field_type')
    def _compute_is_hidden(self):
        for record in self:
            record.is_hidden = record.field_type == 'hidden'

class CredentialCollection(models.Model):
    _name = 'credential.collection'
    _description = 'Credential Collection'

    name = fields.Char(string="Name", required=True)
    group_ids = fields.Many2many('res.groups', string="Groups")

class CredentialManager(models.Model):
    _name = 'credential.manager'
    _description = 'Credential Manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Item Name', required=True, tracking=True)
    user = fields.Char(string='User', placeholder='User', tracking=True)
    password = fields.Char(string='Password', placeholder='Password', tracking=False)  # Visible by default
    url_1 = fields.Char(string='URL 1', placeholder='URL 1', tracking=True)
    url_2 = fields.Char(string='URL 2', placeholder='URL 2', tracking=True)
    url_3 = fields.Char(string='URL 3', placeholder='URL 3', tracking=True)
    url_4 = fields.Char(string='URL 4', placeholder='URL 4', tracking=True)
    ssh_user = fields.Char(string='SSH User', placeholder='SSH User', tracking=True)
    ssh_password = fields.Char(string='SSH Password', placeholder='SSH Password', tracking=False)  # Visible by default
    ip_address = fields.Char(string='IP Address', placeholder='E.g. 192.168.1.1', tracking=True)
    dns = fields.Char(string='DNS', placeholder='E.g. dns.example.com')
    port = fields.Integer(string='Port', placeholder='E.g. 22', tracking=True)
    private_key = fields.Text(string='Private Key', placeholder='Enter the private key')
    
    # New fields for SSH Root
    ssh_root_user = fields.Char(string='SSH Root User', placeholder='SSH Root User', tracking=True)
    ssh_root_password = fields.Char(string='SSH Root Password', placeholder='SSH Root Password', tracking=False)  # Cambio aquí: tracking=False
    ssh_root_ip_address = fields.Char(string='SSH Root IP Address', placeholder='E.g. 192.168.1.1', tracking=True)
    ssh_root_dns = fields.Char(string='SSH Root DNS', placeholder='E.g. root.dns.example.com', tracking=True)
    ssh_root_port = fields.Integer(string='SSH Root Port', placeholder='E.g. 22', tracking=True)
    ssh_root_private_key = fields.Text(string='SSH Root Private Key', placeholder='Enter the SSH root private key', tracking=True)
    
    notes = fields.Text(string='Notes', placeholder='Notes', tracking=True)
    collection_id = fields.Many2one('credential.collection', string='Folder', tracking=True)
    use_2fa = fields.Boolean(string='Enable 2FA', default=False, tracking=True)
    secret_2fa = fields.Char(string='2FA Secret', placeholder='Enter your secret (e.g. Y3PG 4DGQ Y4ND 2D4P...)')
    current_2fa_token = fields.Char(string='Current 2FA Token', compute='_compute_current_2fa_token', store=False)
    custom_fields = fields.One2many('credential.custom.field', 'credential_id', string='Custom Fields')

    @api.model
    def create(self, vals):
        if 'secret_2fa' in vals and vals['secret_2fa']:
            vals['secret_2fa'] = vals['secret_2fa'].replace(' ', '')
        return super(CredentialManager, self).create(vals)

    def write(self, vals):
        # Rastrear cambios de contraseñas antes de escribir
        for record in self:
            record._track_password_changes(vals)
        
        # Código existente para 2FA
        if 'secret_2fa' in vals and vals['secret_2fa']:
            vals['secret_2fa'] = vals['secret_2fa'].replace(' ', '')
        
        return super(CredentialManager, self).write(vals)

    def _compute_current_2fa_token(self):
        for record in self:
            if record.use_2fa and record.secret_2fa:
                try:
                    totp = pyotp.TOTP(record.secret_2fa, interval=30)
                    record.current_2fa_token = totp.now()
                except Exception:
                    record.current_2fa_token = "Invalid Secret"
            else:
                record.current_2fa_token = False

    def verify_2fa(self, code):
        if self.use_2fa and self.secret_2fa:
            try:
                totp = pyotp.TOTP(self.secret_2fa, interval=30)
                return totp.verify(code)
            except Exception:
                return False
        return False

    def _track_password_changes(self, vals):
        """Rastrea los cambios de contraseñas y los guarda en el historial"""
        if not self.id:  # Solo para registros existentes
            return
        
        # Obtener valores anteriores
        old_record = self.browse(self.id)
        changes = {}
        
        # Verificar cambios en cada tipo de contraseña
        if 'password' in vals and vals['password'] != old_record.password and old_record.password:
            changes['password'] = old_record.password
        
        if 'ssh_password' in vals and vals['ssh_password'] != old_record.ssh_password and old_record.ssh_password:
            changes['ssh_password'] = old_record.ssh_password
        
        if 'ssh_root_password' in vals and vals['ssh_root_password'] != old_record.ssh_root_password and old_record.ssh_root_password:
            changes['ssh_root_password'] = old_record.ssh_root_password
        
        # Si hay cambios, crear registro en el historial
        if changes:
            change_type = 'multiple' if len(changes) > 1 else list(changes.keys())[0]
            
            history_vals = {
                'credential_id': self.id,
                'change_type': change_type,
                'old_password': changes.get('password', False),
                'old_ssh_password': changes.get('ssh_password', False),
                'old_ssh_root_password': changes.get('ssh_root_password', False),
            }
            
            self.env['credential.password.history'].create(history_vals)

    def action_view_password_history(self):
        """Abrir wizard para ver el historial de contraseñas"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Password History',
            'res_model': 'password.history.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }

    def add_webpage(self):
        raise UserError("Add webpage function not yet implemented")

    def action_add_custom_field(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'credential.custom.field.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_credential_id': self.id},
        }

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(CredentialManager, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(result['arch'])
            for node in doc.xpath("//group[@name='custom_fields_group']"):
                # Clear existing group
                for child in node.xpath('./field'):
                    node.remove(child)
                # Get active record
                record = self.browse(self._context.get('active_id')) if self._context.get('active_id') else self
                if record:
                    for custom_field in record.custom_fields:
                        # Create field for name
                        field_name_node = etree.Element('field', {
                            'name': 'custom_' + str(custom_field.id),
                            'string': custom_field.name,
                            'invisible': '1' if custom_field.is_hidden else '0'
                        })
                        # Create field for value
                        field_value_node = etree.Element('field', {
                            'name': 'custom_' + str(custom_field.id) + '_value',
                            'string': 'Value',
                            'invisible': '1' if custom_field.is_hidden else '0'
                        })
                        node.append(field_name_node)
                        node.append(field_value_node)
                result['arch'] = etree.tostring(doc, encoding='unicode')
        return result

class CredentialCustomFieldWizard(models.TransientModel):
    _name = 'credential.custom.field.wizard'
    _description = 'Custom Field Wizard'

    credential_id = fields.Many2one('credential.manager', string='Credential', required=True)
    name = fields.Char(string='Name', required=True)
    value = fields.Char(string='Value')
    field_type = fields.Selection([
        ('text', 'Text'),
        ('hidden', 'Hidden'),
        ('boolean', 'Boolean'),
        ('linked', 'Linked')
    ], string='Type', default='text', required=True)
    linked_field = fields.Selection([
        ('user', 'User'),
        ('password', 'Password')
    ], string='Linked Field', required=False)

    def action_save_custom_field(self):
        self.ensure_one()
        custom_field = self.env['credential.custom.field'].create({
            'credential_id': self.credential_id.id,
            'name': self.name,
            'value': self.value,
            'field_type': self.field_type,
            'linked_field': self.linked_field if self.field_type == 'linked' else False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'credential.manager',
            'res_id': self.credential_id.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }

class CredentialAccessWizard(models.TransientModel):
    _name = 'credential.access.wizard'
    _description = '2FA Verification Wizard'

    credential_id = fields.Many2one('credential.manager', string='Credential')
    code_2fa = fields.Char(string='2FA Code', placeholder='2FA Code')

    def verify_and_access(self):
        self.ensure_one()
        credential = self.credential_id
        if credential.use_2fa and not credential.verify_2fa(self.code_2fa):
            raise UserError('Invalid 2FA Code')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'credential.manager',
            'res_id': credential.id,
            'view_mode': 'form',
            'target': 'current',
        }