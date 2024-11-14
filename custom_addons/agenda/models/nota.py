from odoo import models, fields, api
import openai # Asegúrate de tener la biblioteca de OpenAI configurada para este uso
import json

class Nota(models.Model):
    _name = 'agenda.nota'
    _description = 'Nota'

    nroBimestre = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')], string='Bimestre', required=True,default='1')
    nota = fields.Float(string='Nota', required=True)
    observacion = fields.Text(string='Observacion', required=True)
    curso_materia_id = fields.Many2one('agenda.curso_materia', string='Materia', required=True)
    student_id = fields.Many2one('agenda.estudiante', string='Estudiante', required=True)
    boletin_id = fields.Many2one('agenda.boletin', string='Boletín', ondelete='cascade')

    @api.model
    def create(self, vals):
        # Obtiene el estudiante y el bimestre de la nueva nota
        student_id = vals.get('student_id')
        nroBimestre = vals.get('nroBimestre')

        # Verifica si ya existe un boletín para el mismo estudiante y bimestre
        boletin = self.env['agenda.boletin'].search([
            ('student_id', '=', student_id),
            ('nroBimestre', '=', nroBimestre)
        ], limit=1)

        # Si no existe, crea un nuevo boletín
        if not boletin:
            boletin = self.env['agenda.boletin'].create({
                'student_id': student_id,
                'nroBimestre': nroBimestre,
            })

        # Asocia la nueva nota con el boletín encontrado o creado
        vals['boletin_id'] = boletin.id

        # Crea la nueva nota
        nota = super(Nota, self).create(vals)

        # Agrega la nueva nota al boletín
        boletin.write({'Notas': [(4, nota.id)]})
        
        # Generar cuestionario si la nota está entre 41 y 50
        if 41 <= vals.get('nota', 0) <= 50:
            self._generar_cuestionario(nota)

        return nota
    
    def _generar_cuestionario(self, nota):
        prompt = f"""
        Eres un asistente que genera cuestionarios de reforzamiento para estudiantes de primaria. Crea un cuestionario de 10 preugntas sobre el tema que incluya un breve material de reforzamiento, con enlaces de videos de youtube en cualquier idioma. Solo devuelve un JSON en el siguiente formato sin incluir texto adicional:

        {{
            "tema_reforzamiento": "Breve explicación del tema de reforzamiento",
            "enlaces_videos": ["https://youtube.com/example1", "https://youtube.com/example2"],
            "preguntas": [
                {{
                    "contenido": "Pregunta 1",
                    "opciones": ["Opción 1", "Opción 2", "Opción 3", "Opción 4"],
                    "respuesta_correcta": "Opción 1"
                }},
                {{
                    "contenido": "Pregunta 2",
                    "opciones": ["Opción 1", "Opción 2", "Opción 3", "Opción 4"],
                    "respuesta_correcta": "Opción 2"
                }}
            ]
        }}

        Información para el cuestionario:
        - Curso: {nota.curso_materia_id.curso_id.name}
        - Materia: {nota.curso_materia_id.materia_id.name}
        - Observación: {nota.observacion}
        """
        
        
        # Llamada a ChatGPT para generar cuestionario
        try:
            openai.api_key ='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'
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            #respuesta = response['choices'][0]['message']['content']
            respuesta = response.choices[0].message.content
            self._procesar_respuesta_chatgpt(respuesta, nota)
            print('Imprimiendo respuesta:',respuesta)

        except openai.error.OpenAIError as e:
            print(f"Error generando el cuestionario: {e}")

    def _procesar_respuesta_chatgpt(self, result, nota):
        # Limpiar la respuesta eliminando caracteres de bloque de código markdown
        result_cleaned = result.strip('```json').strip('```')
    
        # Intentar cargar el JSON generado por ChatGPT
        try:
            data = json.loads(result_cleaned)
            print('Imprimiendo data:',data)
            
            print('Guardando cuestionario:')
            cuestionario = self.env['agenda.cuestionario'].create({
                'nota_id': nota.id,
                'tema_reforzamiento': data['tema_reforzamiento'],
                'enlaces_videos': json.dumps(data['enlaces_videos']),
            })
            
            print('Guardando Preguntas del cuestionario')
            for pregunta_data in data['preguntas']:
                pregunta = self.env['agenda.pregunta_cuestionario'].create({
                    'cuestionario_id': cuestionario.id,
                    'contenido': pregunta_data['contenido'],
                    'opciones': json.dumps(pregunta_data['opciones']),
                    'respuesta_correcta': pregunta_data['respuesta_correcta'],
                })
            print('Finalizó el guardado')
                
        except json.JSONDecodeError:
            print("Error procesando la respuesta de ChatGPT: No es un JSON válido")
        except KeyError as e:
            print(f"Error en la estructura JSON: Falta la clave {e}")
    