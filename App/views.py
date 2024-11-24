from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.db import connection, transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from .models import *
import base64
import logging



logger = logging.getLogger(__name__)

# @login_required()
def home(request):
    username = request.session.get('username')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM alumnos WHERE username_alumno = %s
        """, [username])
        estudiante = cursor.fetchone() 

    if estudiante:
        context = {
            'nombre': estudiante[1],  
            'carnet': estudiante[0],  
        }
    else:
        messages.error(request, "Estudiante no encontrado")  

        context = {}

    return render(request, 'home.html', context)    

def logout_view(request):
    logout(request)  
    return HttpResponseRedirect("/login")


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username and password:
            with connection.cursor() as cursor:
                cursor.execute("SELECT username, password, tipo FROM Usuario WHERE username = %s", [username])
                user = cursor.fetchone()

                if user:
                    if user[1] == password:
                        tipo = user[2]

                        request.session['username'] = user[0]
                        request.session['tipo'] = tipo

                        if tipo == 1:  # Administrador
                            return redirect("app:gestion_docente")
                        else:
                            next_url = request.GET.get('next', '/')
                            return redirect(next_url)
                    else:
                        messages.error(request, "Usuario o contraseña incorrectos.")
                else:
                    messages.error(request, "Usuario no encontrado.")
        else:
            messages.error(request, "Por favor, complete todos los campos.")
    
    return render(request, 'login.html')

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
            messages.error(request, "El documento no está disponible.")
            return redirect('app:home')  


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

def gestion_usuario(request):
    return render(request, 'gestion_usuario.html')

def gestion_alumno(request):
    context = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT carnet, nombre, username_alumno, ano_ingreso FROM alumnos ORDER BY carnet")
            rows = cursor.fetchall()

        alumnos = [
            {
                "carnet": row[0],
                "nombre": row[1],
                "username": row[2],  
                "ano_ingreso": row[3],
            }
            for row in rows
        ]

        context["alumnos"] = alumnos

    except Exception as e:
        context["error"] = f"No se pudo cargar la lista de alumnos. Error: {str(e)}"

    return render(request, 'gestion_alumno.html', context)


def administrar_alumnos(request, carnet=None):

    if request.method == "POST":
        return _crear_actualizar_alumno(request, carnet)
    elif request.method == "GET":
        return _obtener_alumno(carnet)
    elif request.method == "DELETE":
        return _eliminar_alumno(carnet)

    return redirect("app:gestion_alumno")


def _crear_actualizar_alumno(request, carnet= None):
    """
    Crea o actualiza un alumno en la base de datos.
    """
    datos = request.POST
    nombre = datos.get("nombre")
    username = datos.get("username")
    ano_ingreso = datos.get("anio_ingreso")

    print(datos, nombre, username, ano_ingreso)

    try:
        with transaction.atomic():
            if not carnet: 
                logger.info("Creando un nuevo alumno...")
                with connection.cursor() as cursor:
                    cursor.execute('SELECT * FROM usuario WHERE "username"=%s', [username])
                    if not cursor.fetchone():  
                        cursor.execute(
                            'INSERT INTO usuario("username", nombre, tipo) VALUES (%s, %s, 2)',
                            [username, nombre]
                        )
                    cursor.execute(
                        'INSERT INTO alumnos(nombre, "username_alumno", ano_ingreso) VALUES (%s, %s, %s)',
                        [nombre, username, ano_ingreso]
                    )
                logger.info("Alumno creado exitosamente.")
            else:  
                logger.info(f"Actualizando el alumno con carnet: {carnet}...")
                with connection.cursor() as cursor:
                    cursor.execute(
                        'UPDATE alumnos SET nombre=%s, "username_alumno"=%s, ano_ingreso=%s WHERE carnet=%s',
                        [nombre, username, ano_ingreso, carnet]
                    )
                logger.info("Alumno actualizado exitosamente.")
    except Exception as e:
        logger.error(f"Error al crear/actualizar alumno: {e}")
        return JsonResponse({"error": str(e)}, status=500)

    return redirect("app:gestion_alumno")


def _obtener_alumno(carnet):
    """
    Obtiene los detalles de un alumno específico utilizando consultas SQL puras.
    """
    if not carnet:
        return JsonResponse({"error": "Carnet no proporcionado."}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nombre, username_alumno, ano_ingreso, carnet
                FROM alumnos
                WHERE carnet = %s
            """, [carnet])
            row = cursor.fetchone()

        if row:
            print("Row fetched from database:", row)
            response_data = {
                "nombre": row[0],
                "username": row[1],  
                "ano_ingreso": row[2],
                "carnet": row[3],
            }
            print("Mapped response_data:", response_data)

            return JsonResponse(response_data)
        else:
            return JsonResponse({"error": "Alumno no encontrado."}, status=404)
    except Exception as e:
        logger.error(f"Error al obtener alumno: {e}")
        return JsonResponse({"error": str(e)}, status=500)


def _eliminar_alumno(carnet):
    """
    Elimina un alumno de la base de datos.
    """
    if not carnet:
        return JsonResponse({"error": "Carnet no proporcionado."}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM alumnos WHERE carnet=%s", [carnet])
        logger.info(f"Alumno con carnet {carnet} eliminado exitosamente.")
        return JsonResponse({"success": "Alumno eliminado"})
    except Exception as e:
        logger.error(f"Error al eliminar alumno: {e}")
        return JsonResponse({"error": str(e)}, status=500)


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
        cursor.execute(
            "DELETE FROM documentos WHERE carnet = %s AND tipo_documento = %s",
            [carnet, tipo_documento]
        )
        if cursor.rowcount > 0:
            return JsonResponse({"message": "Documento eliminado correctamente."})
        else:
            return JsonResponse({"message": "No se encontró el documento para eliminar."}, status=404)
