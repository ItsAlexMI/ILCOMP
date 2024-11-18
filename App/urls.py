from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "app"

urlpatterns = [
    path('', views.home, name='home'), 
    path('titulo_otorgado', views.titulo_otorgado, name='Titulo_otorgado'),
    path('certificacion_titulo', views.certificacion_titulo, name='Certificacion_titulo'),
    path('publicacion_gaceta', views.publicacion_gaceta, name='Publicacion_gaceta'),
    path('acta_culminacion', views.acta_culminacion, name='Acta_culminacion'),
    path('plan_estudios', views.plan_estudios, name='Plan_estudios'),
    path('certificado_notas', views.certificado_notas, name='Certificado_notas'),
    path('login/', views.login, name='login'),
    path('gestion_usuario', views.gestion_usuario, name='gestion_usuario'),
    path('gestion_alumno', views.gestion_alumno, name='gestion_alumno'),
    path('gestion_docente/', views.gestion_docente, name='gestion_docente'),
    path('administrar_docente/', views.administrar_docente, name='insertar_docente'),
    path('administrar_docente/<int:id>', views.administrar_docente, name='actualizar_docente'),

    path('gestion_CP', views.gestion_CP, name='gestion_CP'),
    path('gestion_notas', views.gestion_notas, name='gestion_notas'),
    # path('login/',auth_views.LoginView.as_view(template_name='login.html'),
    #     name='login'),
    path('logout/', views.logout_view, name='logout'),


]
