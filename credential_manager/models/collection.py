from odoo import models, fields

class CredentialCollection(models.Model):
    _name = 'credential.collection'
    _description = 'Credential Collection'

    name = fields.Char(string='Nombre', required=True)
    group_ids = fields.Many2many('res.groups', string='Grupos con Acceso')