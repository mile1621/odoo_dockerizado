from odoo import models, fields

class Secretaria(models.Model):
    _name = 'school.secretaria'
    _inherits = {'res.users': 'user_id'}

    user_id = fields.Many2one('res.users', ondelete='cascade', required=True)
    direccion = fields.Char('Dirección')
    telefono = fields.Char('Teléfono')
    sexo = fields.Selection([('male', 'Masculino'), ('female', 'Femenino')], string="Sexo")
