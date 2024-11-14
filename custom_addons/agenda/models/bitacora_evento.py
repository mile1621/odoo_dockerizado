from odoo import models, fields

class Bitacora_Evento(models.Model):
    _name = 'agenda.bitacora_evento'
    _description = 'Bitacora para los eventos'

    id_usuario = fields.Integer(string='id_Usuario', required=True)
    nombre = fields.Char(string='Nombre', required=True)
    clase_usuario = fields.Char(string='Clase de Usuario', required=True)
    evento_id = fields.Many2one('agenda.evento', string='Evento')