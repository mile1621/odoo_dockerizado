from odoo import models, fields, api

class PreguntaCuestionario(models.Model):
    _name = 'agenda.pregunta_cuestionario'
    _description = 'Pregunta del Cuestionario'

    cuestionario_id = fields.Many2one('agenda.cuestionario', string='Cuestionario', ondelete='cascade', required=True)
    contenido = fields.Text(string='Pregunta', required=True)
    opciones = fields.Text(string='Opciones de Respuesta', help='JSON con las opciones de respuesta')
    respuesta_correcta = fields.Char(string='Respuesta Correcta', help='La opción correcta para esta pregunta')
    
    # Relación con las respuestas de los estudiantes
    respuesta_ids = fields.One2many('agenda.respuesta_estudiante', 'pregunta_id', string='Respuestas de Estudiantes')
