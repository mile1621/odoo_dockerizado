from odoo import models, fields

class ObjetivoAviso(models.Model):
    _name = 'agenda.objetivo_aviso'
    _description = 'Objetivo de Aviso'

    user_ids = fields.Many2one('res.users', string='Objetivos')  # Relación Many2many para vincular varios usuarios
    aviso_id = fields.Many2one('agenda.aviso', string='Aviso', ondelete='cascade')  # Relación Many2one con el modelo de Aviso