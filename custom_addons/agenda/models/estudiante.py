from odoo import models, fields,api

class Estudiante(models.Model):
    _name = 'agenda.estudiante'
    _description = 'Estudiante'

    studentcode = fields.Char(string='Código Estudiantil', required=True)
    name = fields.Char(string='Nombre', required=True)
    last_name = fields.Char(string='Apellidos', required=True)
    birth_date = fields.Date(string='Fecha de Nacimiento')
    telefono = fields.Char(string='Teléfono')
    sexo = fields.Selection([('masculino', 'Masculino'), ('femenino', 'Femenino')], string='Sexo')
    apoderado_id = fields.Many2one('agenda.apoderado', string='Apoderado')
    curso_id = fields.Many2one('agenda.curso', string='Curso')
    user_id = fields.Many2one('res.users', ondelete='cascade', required=True, string="Usuario")

    @api.model
    def create(self, vals):
        # Crear un usuario automáticamente si no se proporciona uno
        if not vals.get('user_id'):
            user_vals = {
                'name': vals.get('name'),
                'login': vals.get('name')+ vals.get('studentcode') +'@example.com',  # Puedes generar un login predeterminado
                'password': vals.get('studentcode'),  # Establece una contraseña predeterminada (recomendación: reemplazar en producción)
                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],  # Asigna al grupo de portal
                #'email': vals.get('codigo') + '@example.com'  # Correo predeterminado (reemplazar en producción)
            }
            user = self.env['res.users'].create(user_vals)
            vals['user_id'] = user.id

        return super(Estudiante, self).create(vals)