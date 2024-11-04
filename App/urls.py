from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'), 
    path('titulo_otorgado', views.titulo_otorgado, name='Titulo_otorgado'),
    path('certificacion_titulo', views.certificacion_titulo, name='Certificacion_titulo'),
    path('publicacion_gaceta', views.publicacion_gaceta, name='Publicacion_gaceta'),
    path('acta_culminacion', views.acta_culminacion, name='Acta_culminacion'),
    path('plan_estudios', views.plan_estudios, name='Plan_estudios'),
    path('login', views.login, name='login'),
]
