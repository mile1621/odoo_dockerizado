from odoo import models, fields

class Materia(models.Model):
    _name = 'agenda.materia'
    _description = 'Materia'

    name = fields.Char(string='Nombre', required=True)
