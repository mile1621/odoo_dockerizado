from odoo import models, fields,api

class Curso(models.Model):
    _name = 'agenda.curso'
    _description = 'Curso'

    grado = fields.Char(string='Grado', required=True)
    paralelo = fields.Selection([('A', 'A'), ('B', 'B')], string='Paralelo')
    name = fields.Char(compute="_compute_name")

    @api.depends('grado', 'paralelo')
    def _compute_name(self):
        for record in self:
            # Combina 'grado' y 'paralelo' para generar el nombre completo
            record.name = f"{record.grado} - {record.paralelo}" if record.paralelo else record.grado
