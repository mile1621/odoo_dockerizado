from odoo import models, fields

class AsistenciaAviso(models.Model):
    _name = 'agenda.asistencia_aviso'
    _description = 'Registro de Asistencia para Avisos'

    aviso_id = fields.Many2one('agenda.aviso', string='Aviso', ondelete='cascade', required=True)
    apoderado_id = fields.Many2one('agenda.apoderado', string='Apoderado', ondelete='cascade', required=True)
    fecha_asistencia = fields.Datetime(string='Fecha de Asistencia')  # Se llena solo si el apoderado asiste
    ubicacion_gps_apoderado = fields.Char(string='Ubicación GPS del Apoderado')
    foto_asistencia = fields.Binary(string='Foto de Asistencia')
    confirmado = fields.Boolean(string='Asistencia Confirmada', default=False)  # False al inicio, cambia a True si el apoderado asiste
    metodo_asistencia = fields.Selection([
        ('qr', 'Código QR'),
        ('facial', 'Reconocimiento Facial'),
        ('no_asistencia', 'No Asistió')
    ], string='Método de Asistencia', default='no_asistencia')