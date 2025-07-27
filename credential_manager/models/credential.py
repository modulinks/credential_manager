from odoo import models, fields, api
import pyotp
from odoo.exceptions import UserError

class CredentialCustomField(models.Model):
    _name = 'credential.custom.field'
    _description = 'Campo Personalizado de Credencial'

    credential_id = fields.Many2one('credential.manager', string='Credencial', ondelete='cascade')
    name = fields.Char(string='Nombre', required=True)
    value = fields.Char(string='Valor')
    field_type = fields.Selection([
        ('text', 'Texto'),
        ('hidden', 'Oculto'),
        ('boolean', 'Booleano'),
        ('linked', 'Enlazado')
    ], string='Tipo', default='text', required=True)
    is_hidden = fields.Boolean(compute='_compute_is_hidden', store=False)
    linked_field = fields.Selection([
        ('user', 'Usuario'),
        ('password', 'Contraseña')
    ], string='Campo Enlazado', required=False)

    @api.depends('field_type')
    def _compute_is_hidden(self):
        for record in self:
            record.is_hidden = record.field_type == 'hidden'

class CredentialCollection(models.Model):
    _name = 'credential.collection'
    _description = 'Colección de Credenciales'

    name = fields.Char(string="Nombre", required=True)
    group_ids = fields.Many2many('res.groups', string="Grupos")

class CredentialManager(models.Model):
    _name = 'credential.manager'
    _description = 'Gestor de Credenciales'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre del Elemento', required=True, tracking=True)
    user = fields.Char(string='Usuario', placeholder='Usuario', tracking=True)
    password = fields.Char(string='Contraseña', placeholder='Contraseña', tracking=False)  # Visible por defecto
    url_1 = fields.Char(string='URL 1', placeholder='URL 1', tracking=True)
    url_2 = fields.Char(string='URL 2', placeholder='URL 2')
    url_3 = fields.Char(string='URL 3', placeholder='URL 3')
    url_4 = fields.Char(string='URL 4', placeholder='URL 4')
    ssh_user = fields.Char(string='Usuario SSH', placeholder='Usuario SSH', tracking=True)
    ssh_password = fields.Char(string='Contraseña SSH', placeholder='Contraseña SSH', tracking=True)  # Visible por defecto
    ip_address = fields.Char(string='Dirección IP', placeholder='Ej. 192.168.1.1', tracking=True)
    dns = fields.Char(string='DNS', placeholder='Ej. dns.example.com')
    port = fields.Integer(string='Puerto', placeholder='Ej. 22', tracking=True)
    private_key = fields.Text(string='Clave Privada', placeholder='Ingresa la clave privada')
    
    # Nuevos campos para SSH Root
    ssh_root_user = fields.Char(string='Usuario SSH Root', placeholder='Usuario SSH Root', tracking=True)
    ssh_root_password = fields.Char(string='Contraseña SSH Root', placeholder='Contraseña SSH Root', tracking=True)
    ssh_root_ip_address = fields.Char(string='Dirección IP SSH Root', placeholder='Ej. 192.168.1.1', tracking=True)
    ssh_root_dns = fields.Char(string='DNS SSH Root', placeholder='Ej. root.dns.example.com')
    ssh_root_port = fields.Integer(string='Puerto SSH Root', placeholder='Ej. 22', tracking=True)
    ssh_root_private_key = fields.Text(string='Clave Privada SSH Root', placeholder='Ingresa la clave privada SSH Root')
    
    notes = fields.Text(string='Notas', placeholder='Notas', tracking=True)
    collection_id = fields.Many2one('credential.collection', string='Carpeta', tracking=True)
    use_2fa = fields.Boolean(string='Habilitar 2FA', default=False, tracking=True)
    secret_2fa = fields.Char(string='Secreto 2FA', placeholder='Ingresa tu secreto (ej. Y3PG 4DGQ Y4ND 2D4P...)')
    current_2fa_token = fields.Char(string='Token 2FA Actual', compute='_compute_current_2fa_token', store=False)
    custom_fields = fields.One2many('credential.custom.field', 'credential_id', string='Campos Personalizados')

    @api.model
    def create(self, vals):
        if 'secret_2fa' in vals and vals['secret_2fa']:
            vals['secret_2fa'] = vals['secret_2fa'].replace(' ', '')
        return super(CredentialManager, self).create(vals)

    def write(self, vals):
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
                    record.current_2fa_token = "Secreto inválido"
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

    def add_webpage(self):
        raise UserError("Función de añadir página web aún no implementada")

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
                # Limpiar el grupo existente
                for child in node.xpath('./field'):
                    node.remove(child)
                # Obtener el registro activo
                record = self.browse(self._context.get('active_id')) if self._context.get('active_id') else self
                if record:
                    for custom_field in record.custom_fields:
                        # Crear campo para el nombre
                        field_name_node = etree.Element('field', {
                            'name': 'custom_' + str(custom_field.id),
                            'string': custom_field.name,
                            'invisible': '1' if custom_field.is_hidden else '0'
                        })
                        # Crear campo para el valor
                        field_value_node = etree.Element('field', {
                            'name': 'custom_' + str(custom_field.id) + '_value',
                            'string': 'Valor',
                            'invisible': '1' if custom_field.is_hidden else '0'
                        })
                        node.append(field_name_node)
                        node.append(field_value_node)
                result['arch'] = etree.tostring(doc, encoding='unicode')
        return result

class CredentialCustomFieldWizard(models.TransientModel):
    _name = 'credential.custom.field.wizard'
    _description = 'Wizard para Agregar Campo Personalizado'

    credential_id = fields.Many2one('credential.manager', string='Credencial', required=True)
    name = fields.Char(string='Nombre', required=True)
    value = fields.Char(string='Valor')
    field_type = fields.Selection([
        ('text', 'Texto'),
        ('hidden', 'Oculto'),
        ('boolean', 'Booleano'),
        ('linked', 'Enlazado')
    ], string='Tipo', default='text', required=True)
    linked_field = fields.Selection([
        ('user', 'Usuario'),
        ('password', 'Contraseña')
    ], string='Campo Enlazado', required=False)

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
    _description = 'Wizard para Verificar 2FA'

    credential_id = fields.Many2one('credential.manager', string='Credencial')
    code_2fa = fields.Char(string='Código 2FA', placeholder='Código 2FA')

    def verify_and_access(self):
        self.ensure_one()
        credential = self.credential_id
        if credential.use_2fa and not credential.verify_2fa(self.code_2fa):
            raise UserError('Código 2FA inválido')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'credential.manager',
            'res_id': credential.id,
            'view_mode': 'form',
            'target': 'current',
        }