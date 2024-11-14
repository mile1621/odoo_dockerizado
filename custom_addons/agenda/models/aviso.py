from odoo import models, fields, api
from datetime import datetime

class Aviso(models.Model):
    _name = 'agenda.aviso'
    _description = 'Aviso'

    titulo = fields.Char(string='Título', required=True)
    descripcion = fields.Text(string='Descripción')
    fecha = fields.Date(string='Fecha', required=True)
    tipo_aviso = fields.Selection([('reunion', 'Reunion'), ('comunicado', 'Comunicado')], string='Tipo de Aviso', required=True, default='reunion')
    ubicacion_gps = fields.Char(string='Ubicación GPS', help="Ubicación en formato latitud,longitud (solo para reuniones)")
    hora_finalizacion = fields.Datetime(string='Hora de Finalización', help="Hora límite para registrar asistencia (solo para reuniones)")
    archivo_ids = fields.One2many('agenda.archivo_aviso', 'aviso_id', string="Archivos")
    bitacora_ids = fields.One2many('agenda.bitacora_aviso', 'aviso_id', string="Bitácora")
    objetivo_ids = fields.One2many('agenda.objetivo_aviso', 'aviso_id', string="Objetivos")
    asistencia_ids = fields.One2many('agenda.asistencia_aviso', 'aviso_id', string="Asistencias Registradas")
    # Campo calculado para mostrar el ID
    aviso_id_display = fields.Char(string="ID del Aviso", readonly=True)
    
    @api.model
    def create(self, vals):
        aviso = super(Aviso, self).create(vals)
        # Asigna el ID al campo display después de crear el aviso
        aviso.aviso_id_display = str(aviso.id)
        
        # Si el aviso es una reunión, genera registros de asistencia "no_asistencia" para cada objetivo
        if aviso.tipo_aviso == 'reunion':
            aviso._crear_registros_asistencia_inicial()
        
        # Guarda los cambios para asegurarse de que `aviso_id_display` se actualice en la base de datos
        aviso.write({'aviso_id_display': aviso.aviso_id_display})
        
        return aviso
    
    @api.onchange('tipo_aviso')
    def _onchange_tipo_aviso(self):
        if self.tipo_aviso != 'reunion':
            self.ubicacion_gps = False
            self.hora_finalizacion = False

    def _crear_registros_asistencia_inicial(self):
        """Crea registros de asistencia como 'no_asistencia' para cada objetivo en la reunión."""
        for objetivo in self.objetivo_ids:
            if objetivo.user_ids:
                # Buscar el apoderado correspondiente al user_id en objetivo
                apoderado = self.env['agenda.apoderado'].search([('user_id', '=', objetivo.user_ids.id)], limit=1)
                if apoderado:
                    self.env['agenda.asistencia_aviso'].create({
                        'aviso_id': self.id,
                        'apoderado_id': apoderado.id,
                        'metodo_asistencia': 'no_asistencia',
                        'confirmado': False,
                    })
    
    @api.model
    def validate_qr(self, qr_code, aviso_id):
        # Lógica de validación y registro de asistencia
        print('PRINT DESDE EL MODELO AVISO.PY: se está ejecutando validate_qr')
        apoderado = self.env['agenda.apoderado'].search([('qr_code_value', '=', qr_code)], limit=1)
        if not apoderado:
            print('PRINT DESDE EL MODELO AVISO.PY: Código QR no válido')
            return {'success': False, 'error': 'Código QR no válido'}

        # Buscar el aviso específico por su ID
        aviso = self.search([('id', '=', aviso_id)], limit=1)
        if not aviso:
            print('PRINT DESDE EL MODELO AVISO.PY: Aviso no encontrado para el aviso_id: ', aviso_id)
            return {'success': False, 'error': 'Aviso no encontrado'}

        # Verificar que el apoderado es un objetivo del aviso
        objetivo_user_ids = aviso.objetivo_ids.mapped('user_ids.id')
        print('PRINT DESDE EL MODELO AVISO.PY: IDs de usuario objetivo:', objetivo_user_ids)
        print('PRINT DESDE EL MODELO AVISO.PY: ID de usuario del apoderado:', apoderado.user_id.id)

        if apoderado.user_id.id not in objetivo_user_ids:
            print('PRINT DESDE EL MODELO AVISO.PY: El apoderado no es un objetivo del aviso')
            return {'success': False, 'error': 'El apoderado no es un objetivo del aviso'}
    
        # Verificar que la reunión esté activa y que la hora no haya pasado
        if aviso.tipo_aviso != 'reunion' or (aviso.hora_finalizacion and datetime.now() > aviso.hora_finalizacion):
            print('PRINT DESDE EL MODELO AVISO.PY: La reunión no está activa o ya finalizó')
            return {'success': False, 'error': 'La reunión no está activa o ya finalizó'}
        
        # Buscar el registro de asistencia del apoderado para esta reunión
        asistencia_existente = self.env['agenda.asistencia_aviso'].search([
            ('aviso_id', '=', aviso.id),
            ('apoderado_id', '=', apoderado.id)
        ], limit=1)

        if asistencia_existente and asistencia_existente.confirmado:
            print('PRINT DESDE EL MODELO AVISO.PY: El apoderado ya ha registrado asistencia')
            return {'success': False, 'error': 'El apoderado ya ha registrado asistencia'}

        # Actualizar el registro de asistencia a "asistió"
        asistencia_existente.write({
            'fecha_asistencia': datetime.now(),
            'confirmado': True,
            'metodo_asistencia': 'qr',  # o 'facial' según corresponda
        })
        print('PRINT DESDE EL MODELO AVISO.PY: Asistencia registrada para apoderado con ID', apoderado.id)

        return {'success': True}
    
    def dummy_start_qr_scan(self):
        # Método vacío solo para cumplir con el requerimiento del botón en la vista
        print('PRINT DESDE EL MODELO AVISO.PY: SE PRESIONÓ EL BOTÓN PARA ESCANEAR QR')
        pass