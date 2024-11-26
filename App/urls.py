from django.urls import path
from . import views

app_name = "app"

urlpatterns = [
    # Rutas para la página principal y login
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Gestión de documentos asociados a estudiantes

    # Gestion de usuario.
    path('titulo_otorgado/<int:carnet>/', views.titulo_otorgado, name='Titulo_otorgado'),
    path('certificacion_titulo/<int:carnet>/', views.certificacion_titulo, name='Certificacion_titulo'),
    path('publicacion_gaceta/<int:carnet>/', views.publicacion_gaceta, name='Publicacion_gaceta'),
    path('acta_culminacion/<int:carnet>/', views.acta_culminacion, name='Acta_culminacion'),
    path('plan_estudios/<int:carnet>/', views.plan_estudios, name='Plan_estudios'),
    path('certificado_notas/<int:carnet>/', views.certificado_notas, name='Certificado_notas'),

# Gestión general
    path('gestion_usuario/', views.gestion_usuario, name='gestion_usuario'),
    path('administrar_usuario/', views.administrar_usuario, name='administrar_usuario'),
    path('_crear_actualizar_usuario/', views._crear_actualizar_usuario, name='_crear_actualizar_usuario'),
    path('_obtener_usuario/', views._obtener_usuario, name='_obtener_usuario'),
    path('_eliminar_usuario/', views._eliminar_usuario, name='_eliminar_usuario'),




    path('gestion_alumno/', views.gestion_alumno, name='gestion_alumno'),
    path('administrar_alumnos/<int:carnet>/', views.administrar_alumnos, name='administrar_alumnos'),
    path('_crear_actualizar_alumno/', views._crear_actualizar_alumno, name='_crear_actualizar_alumno'),
    path('_obtener_alumno/', views._obtener_alumno, name='_obtener_alumno'),
    path('_eliminar_alumno/', views._eliminar_alumno, name='_eliminar_alumno'),
    path('gestion_docente/', views.gestion_docente, name='gestion_docente'),
    path('administrar_docente/', views.administrar_docente, name='insertar_docente'),
    path('administrar_docente/<int:id>/', views.administrar_docente, name='actualizar_docente'),
    path('gestion_CP/', views.gestion_CP, name='gestion_CP'),
    path('gestion_notas/', views.gestion_notas, name='gestion_notas'),

    # Operaciones de PDFs
    path('subir_pdf/', views.subir_pdf, name='subir_pdf'),
    path('eliminar_pdf/<int:carnet>/<str:tipo_documento>/', views.eliminar_pdf, name='eliminar_pdf'),
]
