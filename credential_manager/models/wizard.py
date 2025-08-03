from odoo import models, fields, api

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
        # Reload credential.manager form view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'credential.manager',
            'res_id': self.credential_id.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }