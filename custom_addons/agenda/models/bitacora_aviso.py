from odoo import models, fields

class BitacoraAviso(models.Model):
    _name = 'agenda.bitacora_aviso'
    _description = 'Bitácora de Aviso'

    idusuario = fields.Many2one('res.users', string='Usuario')
    nombre = fields.Char(string='Nombre')
    claseusuario = fields.Char(string='Clase de Usuario')
    curso = fields.Char(string='Curso')
    aviso_id = fields.Many2one('agenda.aviso', string='Aviso', ondelete='cascade')
