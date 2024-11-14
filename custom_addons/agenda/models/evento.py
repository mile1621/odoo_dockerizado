from odoo import models, fields,api

class Evento(models.Model):
    _name = 'agenda.evento'
    _description = 'Evento: Tema, Recursos, Reunión'

    titulo = fields.Selection([('tarea', 'Tarea'), ('recurso', 'Recurso'),('reunion', 'Reunion')], string='Titulo')
    descripcion = fields.Text(string='Descripcion', required=True)
    fecha_publicacion = fields.Date(string='Fecha de Publicación',required=True)
    fecha_realizacion = fields.Date(string='Fecha de Realización',required=True)
    curso_materia_id = fields.Many2one('agenda.curso_materia', string='Curso y Materia')
    archivo_ids = fields.One2many('agenda.archivo_evento', 'evento_id', string="Archivos")
    archivos_descarga = fields.Char(string="Enlaces de Descarga", compute="_compute_archivos_descarga")
    bitacora_ids = fields.One2many('agenda.bitacora_evento', 'evento_id', string="Bitacora de Visualizaciones")

    @api.depends('archivo_ids')
    def _compute_archivos_descarga(self):
        for record in self:
            enlaces = []
            for archivo in record.archivo_ids:
                url = f"/web/content/{archivo.id}/ruta/{archivo.name}"
                enlace = f"<a href='{url}' target='_blank'>{archivo.name}</a>"
                enlaces.append(enlace)
            record.archivos_descarga = ', '.join(enlaces) if enlaces else "No hay archivos"
