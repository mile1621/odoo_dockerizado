import json
import jwt
import magic  # Asegúrate de tener python-magic instalado
import mimetypes  # Para detectar tipos de archivo
import base64
from datetime import datetime, timedelta
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessDenied

class MyApiController(http.Controller):
    secret_key = "5f04d9faedcd087e0fd39da321676e258a0196be2e6f314922752ea72b0eaaad"

    @http.route('/get_usuarios_relacionados/<int:aviso_id>', type='http', auth='public', methods=['GET'])
    def get_usuarios_relacionados(self, aviso_id):
        # Buscar el aviso específico
        aviso = request.env['agenda.aviso'].sudo().browse(aviso_id)
        
        # Verificar que el aviso exista
        if not aviso.exists():
            return request.make_response('Aviso no encontrado', status=404)
        
        # Obtener los usuarios relacionados a través de los registros de ObjetivoAviso
        objetivos_aviso = request.env['agenda.objetivo_aviso'].sudo().search([('aviso_id', '=', aviso_id)])
        usuarios_relacionados = objetivos_aviso.mapped('user_ids')

        # Preparar la respuesta en formato JSON
        usuarios_data = [{'id': usuario.id, 'name': usuario.name} for usuario in usuarios_relacionados]
        
        # Crear la respuesta JSON
        return request.make_response(
            json.dumps({'usuarios': usuarios_data}),
            headers={'Content-Type': 'application/json'}
        )
    
    # OBTENER EL TOKEN PARA INICIAR SESIÓN EN MÓVIL
    @http.route('/api/login', type='http', auth="none", methods=['POST'], csrf=False, save_session=False, cors="*")
    def get_token(self):
        byte_string = request.httprequest.data
        data = json.loads(byte_string.decode('utf-8'))
        email = data['email']
        password = data['password']

        try:
            # Autenticar al usuario
            print(f"Intentando autenticación para el usuario con email: {email}")
            user_id = request.session.authenticate(request.db, email, password)
            if not user_id:
                print("Error: Email o contraseña inválidos.")
                return json.dumps({"error": "Invalid email or Password."})

            # Obtener el entorno del usuario autenticado
            env = request.env(user=request.env.user.browse(user_id))

            # Obtener el usuario
            user = env['res.users'].browse(user_id)
            print(f"Usuario autenticado con ID: {user_id} y nombre: {user.name}")

            # Determinar si el usuario es un estudiante o apoderado y obtener el nombre completo
            model_name = None
            user_data = {
                "user_name": None,
                "email": email,
                "ci": None,
                "telefono": None,
                "sexo": None,
                "curso": None,
                "student_code": None,
                "birth_date": None,
                "user_photo": None
            }

            # Comprobar si es un estudiante
            student = env['agenda.estudiante'].sudo().search([('user_id', '=', user.id)], limit=1)
            if student:
                model_name = 'agenda.estudiante'
                user_data.update({
                    "user_name": f"{student.name} {student.last_name}",
                    "sexo": student.sexo,
                    "curso": student.curso_id.name if student.curso_id else None,
                    "student_code": student.studentcode,
                    "birth_date": student.birth_date.isoformat() if student.birth_date else None,
                    "telefono": student.telefono
                })
                print(f"Estudiante detectado: {user_data}")

            # Comprobar si es un apoderado (si no se encontró como estudiante)
            if not model_name:
                guardian = env['agenda.apoderado'].sudo().search([('user_id', '=', user.id)], limit=1)
                if guardian:
                    model_name = 'agenda.apoderado'
                    user_data.update({
                        "user_name": guardian.name,
                        "ci": guardian.ci,
                        "telefono": guardian.telefono,
                        "user_photo": guardian.foto.decode('utf-8') if guardian.foto else None,
                        "qr_code": guardian.qr_code.decode('utf-8') if guardian.qr_code else None
                        #"user_photo": None
                    })
                    if guardian.foto:
                        print("Contenido de la foto (base64, limitado a 10 caracteres):", guardian.foto.decode('utf-8')[:10] + "...")
                    if guardian.qr_code:
                        print("Contenido del QR (base64, limitado a 10 caracteres):", guardian.qr_code.decode('utf-8')[:10] + "...")

            # Verificar si el usuario tiene un rol autorizado
            if not model_name:
                print("Error: Usuario no autorizado para esta aplicación.")
                return json.dumps({"error": "User not authorized for this application."})

            # Generar el token JWT
            payload = {
                'user_id': user_id,
                'email': email,
                'model_name': model_name,
                'exp': datetime.utcnow() + timedelta(hours=1)
            }
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')  # Token expira en 1 hora
            print("Token generado exitosamente")

            # Crear el payload de respuesta directamente sin el envoltorio "data"
            response_payload = {
                'user_id': user_id,
                'email': email,
                'token': token,
                'model_name': model_name,
                **user_data,
                "responsedetail": {
                    "messages": "UserValidated",
                    "messagestype": 1,
                    "responsecode": 200
                }
            }
            # Imprimir el payload con una limitación en la cantidad de caracteres de la imagen para no saturar la consola
            if response_payload.get("user_photo"):
                print("Response payload (con foto limitada):", {**response_payload, "user_photo": response_payload["user_photo"][:10] + "..."})
            else:
                print("Response payload:", response_payload)

            return json.dumps(response_payload)

        except AccessDenied:
            return json.dumps({"error": "Invalid email or Password."})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    # CERRAR SESIÓN EN MÓVIL
    @http.route('/api/logout', type='http', auth="none", methods=['POST'], csrf=False, save_session=False, cors="*")
    def logout(self):
        try:
            # Obtener el token del encabezado de la solicitud
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header:
                return json.dumps({"error": "Token is missing!"})
            
            token = auth_header.split(" ")[1]

            # Decodificar el token JWT para obtener el user_id
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = payload['user_id']

            # Cerrar la sesión del usuario en Odoo
            request.session.logout()

            # Responder con un mensaje de éxito
            response_payload = {
                "responsedetail": {
                    "messages": "UserLoggedOut",
                    "messagestype": 1,
                    "responsecode": 200
                }
            }

            return json.dumps(response_payload)

        except jwt.ExpiredSignatureError:
            return json.dumps({"error": "Token has expired!"})
        except jwt.InvalidTokenError:
            return json.dumps({"error": "Invalid token!"})
        except Exception as e:
            return json.dumps({"error": str(e)})
        
    # OBTENER LA LISTA DE MATERIAS DE UN CURSO
    @http.route('/api/student/subjects', type='http', auth="none", methods=['GET'], csrf=False, cors="*")
    def get_student_subjects(self, user_id):
        try:
            # Verificar que el user_id sea válido
            if not user_id:
                return request.make_response(json.dumps({"error": "user_id parameter is missing"}), headers={'Content-Type': 'application/json'}, status=400)

            # Buscar el estudiante
            student = request.env['agenda.estudiante'].sudo().search([('user_id', '=', int(user_id))], limit=1)
            if not student:
                return request.make_response(json.dumps({"error": "Student not found"}), headers={'Content-Type': 'application/json'}, status=404)

            # Obtener las materias del curso del estudiante
            subjects = request.env['agenda.curso_materia'].sudo().search([('curso_id', '=', student.curso_id.id)])
            subject_data = [{"id": sub.materia_id.id, "name": sub.materia_id.name} for sub in subjects]

            return request.make_response(json.dumps(subject_data), headers={'Content-Type': 'application/json'}, status=200)

        except Exception as e:
            return request.make_response(json.dumps({"error": str(e)}), headers={'Content-Type': 'application/json'}, status=500)

    @http.route('/api/subject/events', type='http', auth="none", methods=['GET'], csrf=False, cors="*")
    def get_subject_events(self, subject_id, user_id=None, student_id=None):
        print("Entrando a la ruta /api/subject/events")
        print("Recibido subject_id:", subject_id)
        print("Recibido user_id:", user_id)
        print("Recibido student_id:", student_id)
        try:
            # Verificar el ID del estudiante en función de los parámetros recibidos
            if student_id:
                # Usar el student_id proporcionado (caso apoderado)
                student = request.env['agenda.estudiante'].sudo().search([('id', '=', int(student_id))], limit=1)
            elif user_id:
                # Usar el user_id (caso estudiante)
                student = request.env['agenda.estudiante'].sudo().search([('user_id', '=', int(user_id))], limit=1)
            else:
                return request.make_response(
                    json.dumps({"error": "student_id or user_id parameter is missing"}), 
                    headers={'Content-Type': 'application/json'}, 
                    status=400
                )

            # Verificar si se encontró el estudiante
            if not student:
                print("Estudiante no encontrado con el ID proporcionado.")
                return request.make_response(
                    json.dumps({"error": "Student not found"}), 
                    headers={'Content-Type': 'application/json'}, 
                    status=404
                )

            # Buscar eventos de la materia y curso
            events = request.env['agenda.evento'].sudo().search([
                ('curso_materia_id.materia_id', '=', int(subject_id)),
                ('curso_materia_id.curso_id', '=', student.curso_id.id)
            ])

            # Generar los datos del evento
            events_data = [{
                "id": event.id,
                "titulo": event.titulo,
                "descripcion": event.descripcion,
                "fecha_publicacion": event.fecha_publicacion.isoformat(),
                "fecha_realizacion": event.fecha_realizacion.isoformat(),
                "archivos_descarga": event.archivos_descarga
            } for event in events]

            print("Eventos encontrados:", events_data)
            return request.make_response(
                json.dumps(events_data), 
                headers={'Content-Type': 'application/json'}, 
                status=200
            )

        except Exception as e:
            print("Error en /api/subject/events:", str(e))
            return request.make_response(
                json.dumps({"error": str(e)}), 
                headers={'Content-Type': 'application/json'}, 
                status=500
            )

        
    # Ruta para obtener el detalle completo de un evento junto con los archivos asociados
    @http.route('/api/event/detail', type='http', auth="none", methods=['GET'], csrf=False, cors="*")
    def get_event_detail(self, event_id):
        try:
            # Buscar el evento con el ID proporcionado
            event = request.env['agenda.evento'].sudo().search([('id', '=', int(event_id))], limit=1)
            if not event:
                return request.make_response(
                    json.dumps({"error": "Event not found"}),
                    headers={'Content-Type': 'application/json'},
                    status=404
                )

            # Construir los datos de los archivos con URLs accesibles
            files_data = []
            for archivo in event.archivo_ids:
                # Obtener el tipo MIME usando magic desde el contenido del archivo
                file_content = base64.b64decode(archivo.image)
                mime = magic.Magic(mime=True)
                mimetype = mime.from_buffer(file_content)
                
                # Obtener el tipo MIME del archivo
                #mimetype, _ = mimetypes.guess_type(archivo.name)
                
                # Generar la URL de descarga para el archivo
                file_url = f"/api/archivo_evento/{archivo.id}"  # Nueva ruta para acceder al archivo
                files_data.append({
                    "name": archivo.name,
                    "url": file_url,
                    "mimetype": mimetype
                })

            # Estructurar la respuesta del evento con archivos
            event_data = {
                "id": event.id,
                "titulo": event.titulo,
                "descripcion": event.descripcion,
                "fecha_publicacion": event.fecha_publicacion.isoformat(),
                "fecha_realizacion": event.fecha_realizacion.isoformat(),
                "archivos": files_data
            }

            return request.make_response(
                json.dumps(event_data),
                headers={'Content-Type': 'application/json'},
                status=200
            )

        except Exception as e:
            return request.make_response(
                json.dumps({"error": str(e)}),
                headers={'Content-Type': 'application/json'},
                status=500
            )
    
    # Nueva ruta para servir los archivos asociados a los eventos
    @http.route('/api/archivo_evento/<int:archivo_id>', type='http', auth="none", methods=['GET'], csrf=False, cors="*")
    def archivo_evento(self, archivo_id):
        # Obtener el archivo `archivo_evento` correspondiente usando el ID
        archivo = request.env['agenda.archivo_evento'].sudo().browse(archivo_id)
        
        if not archivo or not archivo.image:
            return request.not_found()

        # Decodificar el contenido binario del archivo
        file_content = base64.b64decode(archivo.image)
        
        # Definir el tipo MIME del archivo o usar un valor predeterminado
        mime = magic.Magic(mime=True)
        mimetype = mime.from_buffer(file_content)
        print(f"Tipo MIME detectado: {mimetype}")
        #mimetype, _ = mimetypes.guess_type(archivo.name)
        #mimetype = mimetype or "application/octet-stream"
        
        # Retornar el archivo como respuesta HTTP
        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', mimetype),
                #('Content-Disposition', f'inline; filename="{archivo.name}"')
                ('Content-Disposition', f'inline; filename="{archivo_id}"')
            ]
        )
    
    # Nueva ruta para servir los archivos asociados a los avisos
    @http.route('/api/archivo_aviso/<int:archivo_id>', type='http', auth="none", methods=['GET'], csrf=False, cors="*")
    def archivo_aviso(self, archivo_id):
        # Obtener el archivo `archivo_aviso` correspondiente usando el ID
        archivo = request.env['agenda.archivo_aviso'].sudo().browse(archivo_id)
        
        if not archivo or not archivo.image:
            return request.not_found()

        # Decodificar el contenido binario del archivo
        file_content = base64.b64decode(archivo.image)
        
        # Definir el tipo MIME del archivo o usar un valor predeterminado
        mime = magic.Magic(mime=True)
        mimetype = mime.from_buffer(file_content)
        print(f"Tipo MIME detectado: {mimetype}")
        #mimetype, _ = mimetypes.guess_type(archivo.name)
        #mimetype = mimetype or "application/octet-stream"
        
        # Retornar el archivo como respuesta HTTP
        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', mimetype),
                #('Content-Disposition', f'inline; filename="{archivo.name}"')
                ('Content-Disposition', f'inline; filename="{archivo_id}"')
            ]
        )
        
    # Ruta para registrar la visualización de un evento
    @http.route('/api/event/register_view', type='http', auth="none", methods=['POST'], csrf=False, cors="*")
    def register_event_view(self):
        try:
            # Decodificar los datos de la solicitud
            byte_string = request.httprequest.data
            data = json.loads(byte_string.decode('utf-8'))

            # Obtener los datos necesarios del payload
            user_id = data.get('user_id')
            user_name = data.get('user_name')
            user_class = data.get('user_class')
            event_id = data.get('event_id')

            # Verificar que todos los datos necesarios estén presentes
            if not all([user_id, user_name, user_class, event_id]):
                return request.make_response(
                    json.dumps({"error": "Missing required fields"}),
                    headers={'Content-Type': 'application/json'},
                    status=400
                )

            # Verificar si ya existe un registro en la bitácora para este usuario y evento
            existing_log = request.env['agenda.bitacora_evento'].sudo().search_count([
                ('id_usuario', '=', user_id),
                ('evento_id', '=', event_id)
            ])

            # Si ya existe un registro, devolver un mensaje indicando que ya está registrado
            if existing_log > 0:
                print("Visualización ya registrada previamente para el usuario:", user_id, "y evento:", event_id)
                return request.make_response(
                    json.dumps({"message": "Visualización ya registrada previamente"}),
                    headers={'Content-Type': 'application/json'},
                    status=200
                )

            # Si no existe un registro, crear uno nuevo
            print("Registrando nueva visualización para el usuario:", user_id, "y evento:", event_id)
            request.env['agenda.bitacora_evento'].sudo().create({
                'id_usuario': user_id,
                'nombre': user_name,
                'clase_usuario': user_class,
                'evento_id': event_id,
            })

            # Responder con éxito
            return request.make_response(
                json.dumps({"message": "Registro de visualización exitoso"}),
                headers={'Content-Type': 'application/json'},
                status=200
            )

        except Exception as e:
            # Registrar el error en los logs para mayor visibilidad
            request.env.cr.rollback()  # Deshacer cualquier cambio en caso de error
            request.env['ir.logging'].sudo().create({
                'name': 'Error en registro de visualización',
                'type': 'server',
                'dbname': request.env.cr.dbname,
                'level': 'error',
                'message': str(e),
                'path': 'api/event/register_view',
                'func': 'register_event_view',
                'line': 'X'  # Puedes poner un número de línea o dejarlo como referencia general
            })

            return request.make_response(
                json.dumps({"error": str(e)}),
                headers={'Content-Type': 'application/json'},
                status=500
            )
    
    # Ruta para actualizar la foto de perfil del apoderado
    @http.route('/api/update_photo', type='http', auth="none", methods=['POST'], csrf=False, cors="*")
    def update_photo(self):
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            token = request.httprequest.headers.get('Authorization').split(" ")[1]
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            user_id = payload['user_id']
            new_photo = data.get('photo')

            if not new_photo:
                return json.dumps({"error": "Photo data is missing"})

            # Buscar el usuario apoderado por el `user_id`
            user = request.env['agenda.apoderado'].sudo().search([('user_id', '=', user_id)], limit=1)
            
            if user:
                # Guardar la foto y loguearla
                user.foto = new_photo
                print("Foto actualizada para el usuario:", user.name)
                print("Contenido de la foto (base64):", new_photo[:100], "...")  # Muestra solo los primeros 100 caracteres
                return json.dumps({"message": "Profile photo updated successfully"})
            else:
                return json.dumps({"error": "User not found"})

        except Exception as e:
            return json.dumps({"error": str(e)})
        
    # obtener la lista de estudiantes asociados al apoderado:
    @http.route('/api/guardian/children', type='http', auth="none", methods=['GET'], csrf=False, cors="*")
    def get_guardian_children(self, user_id):
        try:
            # Buscar el apoderado
            guardian = request.env['agenda.apoderado'].sudo().search([('user_id', '=', int(user_id))], limit=1)
            if not guardian:
                return request.make_response(json.dumps({"error": "Guardian not found"}), headers={'Content-Type': 'application/json'}, status=404)

            # Obtener los hijos asociados al apoderado
            children = [
                {
                    "id": child.id,
                    "name": f"{child.name} {child.last_name}",
                    "course": child.curso_id.name if child.curso_id else "Sin curso"
                }
                for child in guardian.estudiante_ids
            ]

            return request.make_response(json.dumps(children), headers={'Content-Type': 'application/json'}, status=200)

        except Exception as e:
            return request.make_response(json.dumps({"error": str(e)}), headers={'Content-Type': 'application/json'}, status=500)
        
        
    # Obtener las Materias del Hijo
    @http.route('/api/guardian/child_subjects', type='http', auth="none", methods=['GET'], csrf=False, cors="*")
    def get_child_subjects(self, student_id):
        print("Entrando a la ruta /api/guardian/child_subjects")  # Verificación de entrada a la ruta
        print("Recibido student_id:", student_id)  # Verifica el valor de student_id recibido
        try:
            # Verificar que el student_id sea válido
            if not student_id:
                print("Parámetro student_id está vacío")  # Mensaje si falta el parámetro
                return request.make_response(json.dumps({"error": "student_id parameter is missing"}), headers={'Content-Type': 'application/json'}, status=400)

            # Buscar el estudiante
            student = request.env['agenda.estudiante'].sudo().search([('id', '=', int(student_id))], limit=1)
            if not student:
                print("Estudiante no encontrado con el id:", student_id)  # Mensaje si el estudiante no existe
                return request.make_response(json.dumps({"error": "Student not found"}), headers={'Content-Type': 'application/json'}, status=404)

            # Obtener las materias del curso del estudiante
            subjects = request.env['agenda.curso_materia'].sudo().search([('curso_id', '=', student.curso_id.id)])
            subject_data = [{"id": sub.materia_id.id, "name": sub.materia_id.name} for sub in subjects]
            print("Materias encontradas:", subject_data)  # Muestra las materias obtenidas

            return request.make_response(json.dumps(subject_data), headers={'Content-Type': 'application/json'}, status=200)

        except Exception as e:
            print("Error en /api/guardian/child_subjects:", str(e))  # Muestra cualquier error encontrado
            return request.make_response(json.dumps({"error": str(e)}), headers={'Content-Type': 'application/json'}, status=500)

    # Devolver los avisos en los que el apoderado sea objetivo.
    @http.route('/api/guardian/avisos', type='http', auth="none", methods=['GET'], csrf=False, cors="*")
    def get_guardian_avisos(self, user_id):
        try:
            print("user_id entrante:", user_id)
            # Buscar el apoderado
            guardian = request.env['agenda.apoderado'].sudo().search([('user_id', '=', int(user_id))], limit=1)
            if not guardian:
                return request.make_response(json.dumps({"error": "Guardian not found"}), headers={'Content-Type': 'application/json'}, status=404)

            # Obtener los avisos donde el apoderado es objetivo
            avisos = request.env['agenda.aviso'].sudo().search([('objetivo_ids.user_ids', '=', guardian.user_id.id)])
            avisos_data = [{
                "id": aviso.id,
                "titulo": aviso.titulo,
                "descripcion": aviso.descripcion,
                "fecha": aviso.fecha.isoformat(),
                "tipo_aviso": aviso.tipo_aviso,
                "ubicacion_gps": aviso.ubicacion_gps,
                "hora_finalizacion": aviso.hora_finalizacion.isoformat() if aviso.hora_finalizacion else None
            } for aviso in avisos]

            return request.make_response(json.dumps(avisos_data), headers={'Content-Type': 'application/json'}, status=200)
        except Exception as e:
            return request.make_response(json.dumps({"error": str(e)}), headers={'Content-Type': 'application/json'}, status=500)

    # DEVUELVE LOS DETALLES DE UN AVISO
    @http.route('/api/aviso/detalle', type='http', auth="none", methods=['GET'], csrf=False, cors="*")
    def get_aviso_detail(self, aviso_id, user_id=None):
        try:
            # Buscar el aviso con el ID proporcionado
            aviso = request.env['agenda.aviso'].sudo().search([('id', '=', int(aviso_id))], limit=1)
            if not aviso:
                return request.make_response(
                    json.dumps({"error": "Aviso not found"}),
                    headers={'Content-Type': 'application/json'},
                    status=404
                )

            # Construir los datos de los archivos con URLs accesibles
            files_data = []
            for archivo in aviso.archivo_ids:
                # Obtener el tipo MIME usando magic desde el contenido del archivo
                file_content = base64.b64decode(archivo.image)
                mime = magic.Magic(mime=True)
                mimetype = mime.from_buffer(file_content)

                # Generar la URL de descarga para el archivo
                file_url = f"/api/archivo_aviso/{archivo.id}"  # Nueva ruta para acceder al archivo
                files_data.append({
                    "name": archivo.name,
                    "url": file_url,
                    "mimetype": mimetype
                })

            # Obtener el apoderado basado en el user_id proporcionado
            apoderado = request.env['agenda.apoderado'].sudo().search([('user_id', '=', int(user_id))], limit=1)
            ha_asistido = False  # Valor predeterminado

            if apoderado:
                # Verificar si el apoderado ha registrado asistencia para este aviso
                asistencia = request.env['agenda.asistencia_aviso'].sudo().search([
                    ('aviso_id', '=', aviso.id),
                    ('apoderado_id', '=', apoderado.id)
                ], limit=1)
                ha_asistido = asistencia.confirmado if asistencia else False

            # Estructurar la respuesta del aviso con archivos y estado de asistencia
            aviso_data = {
                "id": aviso.id,
                "titulo": aviso.titulo,
                "descripcion": aviso.descripcion,
                "fecha": aviso.fecha.isoformat(),
                "tipo_aviso": aviso.tipo_aviso,
                "hora_finalizacion": aviso.hora_finalizacion.isoformat() if aviso.hora_finalizacion else None,
                "ubicacion_gps": aviso.ubicacion_gps,
                "archivos": files_data,
                "ha_asistido": ha_asistido
            }

            return request.make_response(
                json.dumps(aviso_data),
                headers={'Content-Type': 'application/json'},
                status=200
            )

        except Exception as e:
            return request.make_response(
                json.dumps({"error": str(e)}),
                headers={'Content-Type': 'application/json'},
                status=500
            )
            
    # Nueva ruta para actualizar el registro de asistencia
    @http.route('/api/actualizar_asistencia', type='http', auth='none', methods=['POST'], csrf=False, cors="*")
    def actualizar_asistencia(self, aviso_id, apoderado_id):
        try:
            # Imprimir los parámetros recibidos
            print('Imprimiendo aviso_id entrante: ', aviso_id)
            print('Imprimiendo apoderado_id entrante: ', apoderado_id)

            # Buscar el apoderado para obtener su user_id
            apoderado = request.env['agenda.apoderado'].sudo().search([('user_id', '=', int(apoderado_id))], limit=1)
            if not apoderado:
                print('Apoderado no encontrado con el ID:', apoderado_id)
                return request.make_response(json.dumps({'success': False, 'message': 'Apoderado no encontrado'}), headers={'Content-Type': 'application/json'}, status=404)

            user_id_apoderado = apoderado.id  # Obtener el user_id del apoderado
            print('user_id correspondiente al apoderado:', user_id_apoderado)
        
            # Buscar el registro de asistencia específico
            asistencia = request.env['agenda.asistencia_aviso'].sudo().search([
                ('aviso_id', '=', int(aviso_id)),
                ('apoderado_id', '=', user_id_apoderado)
            ], limit=1)

            # Validar si el registro existe y aún no está confirmado
            if asistencia:
                print("Registro de asistencia encontrado:", asistencia)
                if not asistencia.confirmado:
                    asistencia.write({
                        'confirmado': True,
                        'fecha_asistencia': fields.Datetime.now(),
                        'metodo_asistencia': 'facial'  # Se establece como asistencia por reconocimiento facial
                    })
                    print('Asistencia actualizada')
                    return request.make_response(
                        json.dumps({'success': True, 'message': 'Asistencia actualizada'}),
                        headers={'Content-Type': 'application/json'},
                        status=200
                    )
                else:
                    print("Asistencia ya registrada.")
                    return request.make_response(
                        json.dumps({'success': False, 'message': 'Asistencia ya registrada'}),
                        headers={'Content-Type': 'application/json'},
                        status=200
                    )

            print('Registro de asistencia no encontrado')
            return request.make_response(
                json.dumps({'success': False, 'message': 'Asistencia ya registrada o no encontrada'}),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        except Exception as e:
            # Imprimir el error en caso de excepción
            print('Error al actualizar asistencia:', str(e))
            return request.make_response(
                json.dumps({'success': False, 'error': str(e)}),
                headers={'Content-Type': 'application/json'},
                status=500
            )
            
    # obtener los cuestionarios para un estudiante
    @http.route('/api/cuestionarios', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    def get_cuestionarios(self, user_id):
        #user_id = request.params.get('user_id')
        
        if not user_id:
            return json.dumps({"error": "user_id is missing"})
        
        try:
            user_id = int(user_id)  # Asegurarse de que user_id es un entero
        except ValueError:
            return json.dumps({"error": "Invalid user_id"})

        cuestionarios = request.env['agenda.cuestionario'].sudo().search([
            ('nota_id.student_id.user_id', '=', user_id),
            ('estado', '=', 'pendiente')
        ])

        cuestionarios_data = [{
            'id': cuestionario.id,
            'tema_reforzamiento': cuestionario.tema_reforzamiento,
            'materia': cuestionario.nota_id.curso_materia_id.materia_id.name,
            'fecha_generacion': cuestionario.fecha_generacion.strftime('%Y-%m-%d %H:%M:%S'),
            'estado': cuestionario.estado
        } for cuestionario in cuestionarios]

        #response_data = json.dumps({'cuestionarios': cuestionarios_data})
        return request.make_response(json.dumps(cuestionarios_data), headers={'Content-Type': 'application/json'}, status=200)
    
    # Obtener detalles de un cuestionario específico
    @http.route('/api/cuestionario_detalle/', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    def get_cuestionario_detalle(self, cuestionario_id):
        
        #cuestionario_id = request.params.get('cuestionario_id')  # Asegúrate de recibir cuestionario_id
        print('Id del cuestionario entrante:',cuestionario_id)
        #cuestionario = request.env['agenda.cuestionario'].sudo().browse(cuestionario_id)
        cuestionario = request.env['agenda.cuestionario'].sudo().search([('id', '=', int(cuestionario_id))], limit=1)

        if not cuestionario.exists():
            print('No se encontró el cuestionario con ID:',cuestionario_id)
            return request.make_response(
                        json.dumps({"error": "Cuestionario not found"}),
                        headers={'Content-Type': 'application/json'},
                        status=404
                    )

        print('Obteniendo las preguntas del cuestionario')
        preguntas_data = [{
            'id': pregunta.id,
            'contenido': pregunta.contenido,
            'opciones': json.loads(pregunta.opciones),
            'respuesta_correcta': pregunta.respuesta_correcta
        } for pregunta in cuestionario.pregunta_ids]

        print('Uniendo preguntas con cuestionario')
        cuestionario_data = {
            'id': cuestionario.id,
            'tema_reforzamiento': cuestionario.tema_reforzamiento,
            'enlaces_videos': json.loads(cuestionario.enlaces_videos),
            'materia': cuestionario.nota_id.curso_materia_id.materia_id.name,
            'fecha_generacion': cuestionario.fecha_generacion.strftime('%Y-%m-%d %H:%M:%S'),
            'estado': cuestionario.estado,
            'puntaje_obtenido': cuestionario.puntaje_obtenido,
            'preguntas': preguntas_data
        }
        print('Imprimiendo cuestionario con sus preguntas', cuestionario_data)

        return request.make_response(json.dumps(cuestionario_data), headers={'Content-Type': 'application/json'}, status=200)

    # Ruta para finalizar el cuestionario
    @http.route('/api/finalizar_cuestionario', type='http', auth='none', methods=['POST'], csrf=False, cors="*")
    def finalizar_cuestionario(self):
        try:
            # Decodificar los datos JSON manualmente
            data = json.loads(request.httprequest.data.decode('utf-8'))
            cuestionario_id = data.get('cuestionario_id')
            respuestas = data.get('respuestas')

            print('cuestionario_id entrante: ',cuestionario_id)
            print('respuestas entrante: ',respuestas)
            cuestionario = request.env['agenda.cuestionario'].sudo().search([('id', '=', int(cuestionario_id))], limit=1)
            
            if not cuestionario.exists():
                print('No se encontró el cuestionario: ',cuestionario_id)
                return request.make_response(
                    json.dumps({"error": "Cuestionario no encontrado"}), 
                    headers={'Content-Type': 'application/json'}, 
                    status=404
                )
            
            # Aquí se pueden procesar las respuestas y calcular la puntuación
            print('Calculando puntuación')
            puntaje_obtenido = sum(1 for pregunta_id, respuesta in respuestas.items()
                                if respuesta == cuestionario.pregunta_ids.filtered(lambda p: p.id == int(pregunta_id)).respuesta_correcta)

            # Actualizar el estado del cuestionario y el puntaje obtenido
            print('Puntuación obtenida:', puntaje_obtenido)
            print('Actualizando cuestionario')
            cuestionario.write({
                'estado': 'completado',
                'puntaje_obtenido': puntaje_obtenido,
            })
            print('Actualización Exitosa de cuestionario')
            
            # Obtener la nota bimestral asociada y actualizarla
            nota = cuestionario.nota_id
            if nota:
                nueva_nota = nota.nota + puntaje_obtenido
                nota.write({'nota': nueva_nota})
                print(f'Nota bimestral actualizada a {nueva_nota} para el estudiante {nota.student_id.name}')
            
            print('Actualización Exitosa de cuestionario y nota bimestral')
            return request.make_response(
                json.dumps({"message": "Cuestionario completado con éxito", "puntaje_obtenido": puntaje_obtenido}), 
                headers={'Content-Type': 'application/json'}, 
                status=200
            )

        except Exception as e:
            print('Imprimiendo error: ', str(e))
            return request.make_response(
                json.dumps({"error": str(e)}), 
                headers={'Content-Type': 'application/json'}, 
                status=500
            )