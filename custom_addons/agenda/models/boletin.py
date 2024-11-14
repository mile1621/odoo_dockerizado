from odoo import models, fields

class Boletin(models.Model):
    _name = 'agenda.boletin'
    _description = 'Boletín por estudiante y bimestre'

    Notas = fields.One2many('agenda.nota', 'boletin_id', string='Notas')
    student_id = fields.Many2one('agenda.estudiante', string='Estudiante', required=True)
    nroBimestre = fields.Selection([('1', '1'), ('2', '2'), ('3', '3')], string='Bimestre', required=True)