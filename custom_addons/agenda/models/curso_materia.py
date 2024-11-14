from odoo import models, fields

class Curso_Materia(models.Model):
    _name = 'agenda.curso_materia'
    _description = 'Curso de una materia'

    curso_id = fields.Many2one('agenda.curso', string='Curso')
    profesor_id = fields.Many2one('agenda.profesor', string='Profesor')
    materia_id = fields.Many2one('agenda.materia', string='Materia')
    name = fields.Char(compute="_compute_name")

    def _compute_name(self):
        for rec in self:
            rec.name = str(rec.curso_id.name) +" "+ str(rec.materia_id.name)

    def action_open_notas_by_curso(self):
        # Acción para abrir la vista de notas filtrada por curso_materia_id
        return {
            'name': 'Notas para ' + self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'agenda.nota',
            'view_mode': 'tree,form',
            'domain': [('curso_materia_id', '=', self.id)],  # Filtra notas por el curso seleccionado
            'context': {'default_curso_materia_id': self.id},  # Contexto para crear nota en este curso
        }
