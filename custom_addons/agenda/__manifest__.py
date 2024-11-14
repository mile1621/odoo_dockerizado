{
    'name': 'Agenda Electrónica',
    'version': '1.0',
    'author':'Group 10',
    'category':'Education',
    'summary': 'Manage agenda administration',
    'description': """
        Module to manage agenda administration of a school.
    """,
    'depends': ['mail', 'account', 'base', 'hr', 'web'],
    'category':'Education',
    'data': [
        'views/menu.xml',
        'views/profesor.xml',
        'views/estudiante.xml',
        'views/apoderado.xml',
        'views/evento.xml',
        #'views/ejemplo.xml',
        'views/aviso.xml',
        'views/nota.xml',
        'views/boletin.xml',
        'data/curso.xml',
        'data/materia.xml',
        # 'views/nota_curso_materia.xml',
        'data/apoderado_estudiante.xml',
        'views/curso_materia.xml',

        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'agenda/static/src/js/qr_scanner.js',  # Archivo para marcar asistencia con QR
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
