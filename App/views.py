from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from .models import *

# Create your views here.
# @login_required()
def home(request):
    return render(request, 'home.html')

def logout_view(request):
    logout(request)  # Cerrar sesión correctamente
    return HttpResponseRedirect("/login")


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username and password:
            with connection.cursor() as cursor:
                # Realizamos la consulta para obtener el usuario
                cursor.execute("SELECT username, password, tipo FROM Usuario WHERE username = %s", [username])
                user = cursor.fetchone()

                if user:
                    # Comprobamos que la contraseña coincida
                    if user[1] == password:
                        tipo = user[2]

                        # Guardamos la información del usuario en la sesión
                        request.session['username'] = user[0]
                        request.session['tipo'] = tipo

                        # Verificamos el tipo de usuario y redirigimos
                        if tipo == 1:  # Administrador
                            return redirect("app:gestion_docente")
                        else:
                            # Obtener la URL 'next' si existe, sino redirigir a la raíz
                            next_url = request.GET.get('next', '/')
                            return redirect(next_url)
                    else:
                        messages.error(request, "Usuario o contraseña incorrectos.")
                else:
                    messages.error(request, "Usuario no encontrado.")
        else:
            messages.error(request, "Por favor, complete todos los campos.")
    
    return render(request, 'login.html')

def titulo_otorgado(request):
    return render(request, 'titulo_otorgado.html')

def certificacion_titulo(request):
    return render(request, 'certificacion_titulo.html')

def publicacion_gaceta(request):
    return render(request, 'publicacion_gaceta.html')

def acta_culminacion(request):
    return render(request, 'acta_culminacion.html')

def plan_estudios(request):
    return render(request, 'plan_estudios.html')

def certificado_notas(request):
    return render(request, 'certificado_notas.html')

def gestion_usuario(request):
    return render(request, 'gestion_usuario.html')

def gestion_alumno(request):
    return render(request, 'gestion_alumno.html')

def gestion_docente(request):
    # with connection.cursor() as cursor:
    #     # cursor.execute("UPDATE bar SET foo = 1 WHERE baz = %s", [self.baz])
    #     cursor.execute("SELECT * FROM docente")
    #     row = cursor.fetchone()
    context = {}
    print("Iniciando")
    objs = docente.objects.raw("SELECT * FROM docente order by id")
    # for obj in objs:
    #     print(obj)

    context["docentes"] = objs
    print("Finalizando")
    return render(request, 'gestion_docente.html',context)


def administrar_docente(request,id=None):

    if request.method == "POST":
        datos = request.POST
        # print(datos)
        nombre = datos.get("nombre")
        username = datos.get("username")
        password = datos.get("password")
        print(nombre,username,password)
        if not id:
            # print("Vamos a Insertar")
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM usuario where username=%s",[username])
                row = cursor.fetchone()
                print(row)
                if not row:
                    cursor.execute("insert into usuario(username,nombre,password,tipo) values (%s,%s,%s,0)", [username,nombre,password])

                cursor.execute("insert into docente(nombre,username) values(%s,%s)", [nombre,username])
        else:
            with connection.cursor() as cursor:
                cursor.execute("update docente set nombre=%s,username=%s where id=%s",[nombre,username,id])

    if request.method == "GET":
        objs = docente.objects.raw("SELECT * FROM docente where id=%s",[id])
        # print(objs)
        for o in objs:
        #     print(o.id,o.nombre,o.username)
            r = {"nombre":o.nombre,"id":o.id,"username":o.username}
        return JsonResponse(r)

    if request.method == "DELETE":
        if id:
             with connection.cursor() as cursor:
                cursor.execute("delete from docente where id=%s",[id])

    return redirect("app:gestion_docente")


def gestion_CP(request):
    return render(request, 'gestion_CP.html')

def gestion_notas(request):
    return render(request, 'gestion_notas.html')