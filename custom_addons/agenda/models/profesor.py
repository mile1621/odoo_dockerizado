from odoo import models, fields

class Profesor(models.Model):
    _name = 'agenda.profesor'
    _inherits = {'res.users': 'user_id'}
    _description = 'Modelo de Profesores'

    user_id = fields.Many2one('res.users', ondelete='cascade', required=True)
    codigo = fields.Char('Código')
    direccion = fields.Char('Dirección')
    telefono = fields.Char('Teléfono')
    sexo = fields.Selection([('male', 'Masculino'), ('female', 'Femenino')], string="Sexo")