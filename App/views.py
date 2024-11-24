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
    context = {}
    try:
        objs = Alumnos.objects.raw("SELECT * FROM alumnos ORDER BY carnet")
        context["alumnos"] = objs
    except Exception as e:
        context["error"] = "No se pudo cargar la lista de alumnos."
    return render(request, 'gestion_alumno.html', context)

# ==========================
# Vista: Administrar Alumnos
# ==========================
def administrar_alumnos(request, carnet=None):

    if request.method == "POST":
        return _crear_actualizar_alumno(request, carnet)
    elif request.method == "GET":
        return _obtener_alumno(carnet)
    elif request.method == "DELETE":
        return _eliminar_alumno(carnet)

    return redirect("app:gestion_alumno")

# ==============================
# Funciones auxiliares
# ==============================

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
            if not carnet:  # Crear un nuevo alumno
                logger.info("Creando un nuevo alumno...")
                with connection.cursor() as cursor:
                    cursor.execute('SELECT * FROM usuario WHERE "username"=%s', [username])
                    if not cursor.fetchone():  # Verificar si el usuario no existe
                        cursor.execute(
                            'INSERT INTO usuario("username", nombre, tipo) VALUES (%s, %s, 2)',
                            [username, nombre]
                        )
                    cursor.execute(
                        'INSERT INTO alumnos(nombre, "username_alumno", ano_ingreso) VALUES (%s, %s, %s)',
                        [nombre, username, ano_ingreso]
                    )
                logger.info("Alumno creado exitosamente.")
            else:  # Actualizar un alumno existente
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
    Obtiene los detalles de un alumno específico.
    """
    if not carnet:
        return JsonResponse({"error": "Carnet no proporcionado."}, status=400)

    try:
        alumno = Alumnos.objects.filter(carnet=carnet).first()
        if alumno:
            response_data = {
                "nombre": alumno.nombre,
                "username": alumno.username_alumno,
                "ano_ingreso": alumno.ano_ingreso,
                "carnet": alumno.carnet,
            }
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
