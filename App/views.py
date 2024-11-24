from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from .models import *
import base64

# Create your views here.
# @login_required()
def home(request):
    # Obtener el nombre de usuario del estudiante desde la sesión
    username = request.session.get('username')

    # Realizar la consulta SQL directamente a la base de datos
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM alumnos WHERE username_alumno = %s
        """, [username])
        estudiante = cursor.fetchone()  # Obtiene el primer resultado, si existe

    # Si encontramos al estudiante, mandamos toda su información
    if estudiante:
        context = {
            'nombre': estudiante[1],  # Asumiendo que la columna 1 es 'nombre'
            'carnet': estudiante[0],  # Asumiendo que la columna 0 es 'carnet' (ya que el carnet es único)
        }
    else:
        messages.error(request, "Estudiante no encontrado")  # Usar el sistema de mensajes de Django

        context = {}

    return render(request, 'home.html', context)    

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

# Función para mostrar PDFs
def mostrar_pdf_estudiante(request, carnet, tipo_documento):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT contenido FROM documentos WHERE carnet = %s AND tipo_documento = %s",
            [carnet, tipo_documento]
        )
        row = cursor.fetchone()
        
        if row:
            pdf_content = base64.b64decode(row[0])
            response = HttpResponse(pdf_content, content_type='application/pdf')
            return response
        else:
            # Si el documento no está disponible, redirige con un mensaje de error
            messages.error(request, "El documento no está disponible.")
            return redirect('app:home')  # Asegúrate de tener la URL correcta


# Vistas específicas para cada tipo de documento
def titulo_otorgado(request, carnet):
    return mostrar_pdf_estudiante(request, carnet, "titulo_otorgado")

def certificacion_titulo(request, carnet):
    return mostrar_pdf_estudiante(request, carnet, "certificacion_titulo")

def publicacion_gaceta(request, carnet):
    return mostrar_pdf_estudiante(request, carnet, "publicacion_gaceta")

def acta_culminacion(request, carnet):
    return mostrar_pdf_estudiante(request, carnet, "acta_culminacion")

def plan_estudios(request, carnet):
    return mostrar_pdf_estudiante(request, carnet, "plan_estudios")

def certificado_notas(request, carnet):
    return mostrar_pdf_estudiante(request, carnet, "certificado_notas")

# Vistas de gestión de usuarios y docentes
def gestion_usuario(request):
    return render(request, 'gestion_usuario.html')

def gestion_alumno(request):
    return render(request, 'gestion_alumno.html')

def gestion_docente(request):
    context = {}
    objs = docente.objects.raw("SELECT * FROM docente ORDER BY id")
    context["docentes"] = objs
    return render(request, 'gestion_docente.html', context)

def administrar_docente(request, id=None):
    if request.method == "POST":
        datos = request.POST
        nombre = datos.get("nombre")
        username = datos.get("username")
        password = datos.get("password")
        
        if not id:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM usuario WHERE username = %s", [username])
                row = cursor.fetchone()
                if not row:
                    cursor.execute("INSERT INTO usuario(username, nombre, password, tipo) VALUES (%s, %s, %s, 0)", 
                                   [username, nombre, password])
                cursor.execute("INSERT INTO docente(nombre, username) VALUES (%s, %s)", [nombre, username])
        else:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE docente SET nombre=%s, username=%s WHERE id=%s", [nombre, username, id])

    elif request.method == "GET":
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM docente WHERE id = %s", [id])
            row = cursor.fetchone()
            if row:
                r = {"nombre": row[1], "id": row[0], "username": row[2]}
                return JsonResponse(r)

    elif request.method == "DELETE":
        if id:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM docente WHERE id=%s", [id])

    return redirect("app:gestion_docente")

# Vista para subir PDFs
def subir_pdf(request):
    if request.method == "POST":
        carnet = request.POST.get("carnet")
        tipo_documento = request.POST.get("tipo_documento")
        archivo = request.FILES.get("archivo")

        if carnet and tipo_documento and archivo:
            contenido = archivo.read()
            pdf_base64 = base64.b64encode(contenido).decode('utf-8')

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO documentos (carnet, tipo_documento, contenido)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (carnet, tipo_documento) DO UPDATE 
                    SET contenido = EXCLUDED.contenido
                    """,
                    [carnet, tipo_documento, pdf_base64]
                )
                messages.success(request, "Archivo subido correctamente.")
        else:
            messages.error(request, "Por favor, complete todos los campos y cargue un archivo válido.")

    return render(request, "subir_pdf.html")


def gestion_CP(request):
    return render(request, 'gestion_CP.html')

def gestion_notas(request):
    return render(request, 'gestion_notas.html')

def eliminar_pdf(request, carnet, tipo_documento):
    with connection.cursor() as cursor:
        # Intentamos eliminar el documento
        cursor.execute(
            "DELETE FROM documentos WHERE carnet = %s AND tipo_documento = %s",
            [carnet, tipo_documento]
        )
        # Comprobamos si la eliminación fue exitosa
        if cursor.rowcount > 0:
            return JsonResponse({"message": "Documento eliminado correctamente."})
        else:
            return JsonResponse({"message": "No se encontró el documento para eliminar."}, status=404)
