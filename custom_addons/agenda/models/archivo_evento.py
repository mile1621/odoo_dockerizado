from odoo import models, fields,api


class Archivo_Evento(models.Model):
    _name = 'agenda.archivo_evento'
    _description = 'Archivos para los eventos'

    name = fields.Char(string='Nombre', required = True)
    # ruta = fields.Binary(string='Archivo')
    ruta = fields.Char(string='URL de Acceso', compute='_compute_ruta', store=True)  # Guardará la URL pública del archivo
    image = fields.Binary(string="Imagen")
    evento_id = fields.Many2one('agenda.evento', string='Evento')

    @api.depends('image')
    def _compute_ruta(self):
     for record in self:
        if record.image:
            # Genera una URL pública usando el controlador personalizado
            record.ruta = f"/archivo_evento/{record.id}"
        else:
            record.ruta = ""
    # @api.model
    # def create(self, vals):
    #     # Si se sube una imagen, guarda el archivo en el sistema y actualiza la ruta
    #     if vals.get('image'):
    #         # Decodificar la imagen
    #         image_data = base64.b64decode(vals['image'])

    #         # Definir la ruta del archivo
    #         filename = f"{vals.get('nombre', 'archivo')}.png"  # Puedes cambiar la extensión según el tipo de imagen
    #         file_path = os.path.join('addons', 'agenda', 'static', 'files', filename)

    #         # Crear la carpeta si no existe
    #         os.makedirs(os.path.dirname(file_path), exist_ok=True)

    #         # Guardar la imagen en el sistema de archivos
    #         with open(file_path, 'wb') as f:
    #             f.write(image_data)

    #         # Actualizar la ruta en los valores
    #         vals['ruta'] = file_path

    #     return super(Archivo_Evento, self).create(vals)