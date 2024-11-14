from odoo import models, fields, api

class ArchivoAviso(models.Model):
    _name = 'agenda.archivo_aviso'
    _description = 'Archivo para Aviso'

    name = fields.Char(string='Nombre', required = True)
    ruta = fields.Char(string='URL de Acceso', compute='_compute_ruta', store=True)  # Guardará la URL pública del archivo
    image = fields.Binary(string="Imagen")
    aviso_id = fields.Many2one('agenda.aviso', string='Aviso', ondelete='cascade')

    @api.depends('image')
    def _compute_ruta(self):
     for record in self:
        if record.image:
            # Genera una URL pública usando el controlador personalizado
            record.ruta = f"/archivo_aviso/{record.id}"
        else:
            record.ruta = ""