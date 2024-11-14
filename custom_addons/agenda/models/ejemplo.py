from odoo import models, fields

class Post(models.Model):
    _name = 'website.post'
    _description = 'Website Post'

    title = fields.Char(string="Título", required=True)
    subtitle = fields.Char(string="Subtítulo")
    content = fields.Text(string="Contenido")
    image = fields.Binary(string="Imagen")
    image_caption = fields.Char(string="Leyenda de la imagen")
    author = fields.Char(string="Autor")
