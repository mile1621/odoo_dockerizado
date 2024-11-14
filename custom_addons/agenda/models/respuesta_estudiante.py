from odoo import models, fields, api

class RespuestaEstudiante(models.Model):
    _name = 'agenda.respuesta_estudiante'
    _description = 'Respuesta del Estudiante'

    pregunta_id = fields.Many2one('agenda.pregunta_cuestionario', string='Pregunta', ondelete='cascade', required=True)
    respuesta_seleccionada = fields.Char(string='Respuesta Seleccionada', required=True)
    correcta = fields.Boolean(string='Es Correcta', compute='_compute_correcta', store=True)

    @api.depends('respuesta_seleccionada', 'pregunta_id')
    def _compute_correcta(self):
        for record in self:
            record.correcta = record.respuesta_seleccionada == record.pregunta_id.respuesta_correcta
