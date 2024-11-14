from odoo import models, fields,api
import qrcode
import base64
from io import BytesIO

class Apoderado(models.Model):
    _name = 'agenda.apoderado'
    _description = 'Apoderado'

    ci = fields.Char(string='CI', required=True)
    name = fields.Char(string='Nombre', required=True)
    email = fields.Char(string='Email', required=True)
    foto = fields.Binary(string='Foto')
    qr_code = fields.Binary(string='Código QR', compute='_generate_qr_code', store=True)
    qr_code_value = fields.Char(string='Valor del Código QR', compute='_generate_qr_code', store=True)  # Nuevo campo
    telefono = fields.Char(string='Teléfono')
    estudiante_ids = fields.One2many('agenda.estudiante', 'apoderado_id', string='Hijos')
    user_id = fields.Many2one('res.users', ondelete='cascade', required=True, string="Usuario")

    @api.model
    def create(self, vals):
        # Crear un usuario automáticamente si no se proporciona uno
        if not vals.get('user_id'):
            user_vals = {
                'name': vals.get('name'),
                'login': vals.get('email'),  # Puedes generar un login predeterminado
                'password': vals.get('ci'),  # Establece una contraseña predeterminada (recomendación: reemplazar en producción)
                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],  # Asigna al grupo de portal
                'email': vals.get('email')
            }
            user = self.env['res.users'].create(user_vals)
            vals['user_id'] = user.id

        return super(Apoderado, self).create(vals)
    
    @api.depends('ci')
    def _generate_qr_code(self):
        for record in self:
            # Crear el contenido del QR basado en el CI
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(record.ci)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            
            # Convertir la imagen a base64 para almacenarla
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            record.qr_code = base64.b64encode(buffer.getvalue())
            record.qr_code_value = record.ci  # Guardar el valor del QR como texto
