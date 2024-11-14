from odoo import models, fields, api

class Cuestionario(models.Model):
    _name = 'agenda.cuestionario'
    _description = 'Cuestionario para Reforzamiento y Repechaje'

    nota_id = fields.Many2one('agenda.nota', string='Nota', required=True, ondelete='cascade')
    fecha_generacion = fields.Datetime(string='Fecha de Generación', default=fields.Datetime.now)
    estado = fields.Selection([('pendiente', 'Pendiente'), ('completado', 'Completado')], string='Estado', default='pendiente')
    puntaje_obtenido = fields.Integer(string='Puntaje Obtenido', default=0)
    
    # Material de reforzamiento
    tema_reforzamiento = fields.Char(string='Tema de Reforzamiento', help='Un tema breve de reforzamiento')
    enlaces_videos = fields.Text(string='Enlaces de Videos', help='URLs de videos de YouTube o enlaces relevantes')
    
    # Relación con las preguntas del cuestionario
    pregunta_ids = fields.One2many('agenda.pregunta_cuestionario', 'cuestionario_id', string='Preguntas')
