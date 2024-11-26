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

def login_required_custom(view_func):
    """
    Función decoradora personalizada que redirige al login si el usuario no está autenticado.
    """
    def _wrapped_view(request, *args, **kwargs):
        # Verificar si el usuario está autenticado
        if not request.session.get('username'):
            messages.error(request, "Por favor, inicie sesión para acceder a esta página.")
            return redirect('app:login')  # Redirige a la página de login

        # Si el usuario está autenticado, se ejecuta la vista
        return view_func(request, *args, **kwargs)

    return _wrapped_view

def layout(request):
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
    return render(request, 'layout.html', context)



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
                        else:          # Estudiante
                            return redirect("app:home")
                    else:
                        messages.error(request, "Usuario o contraseña incorrectos.")
                else:
                    messages.error(request, "Usuario no encontrado.")
        else:
            messages.error(request, "Por favor, complete todos los campos.")
    
    return render(request, 'login.html')


@login_required_custom
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

@login_required_custom
def gestion_usuario(request):
    context = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT username, nombre, tipo FROM usuario ORDER BY nombre")
            rows = cursor.fetchall()

        usuarios = [
            {
                "username": row[0],
                "nombre": row[1],
                "tipo": row[2],
            }
            for row in rows
        ]

        context["usuarios"] = usuarios

    except Exception as e:
        context["error"] = f"No se pudo cargar la lista de usuarios. Error: {str(e)}"
    return render(request, 'gestion_usuario.html', context)

def administrar_usuario(request, username=None):
    if request.method == "POST":
        return _crear_actualizar_usuario(request, username)
    elif request.method == "GET":
        return _obtener_usuario(username)
    elif request.method == "DELETE":
        return _eliminar_usuario(username)

    return redirect("app:gestion_usuario")


def _crear_actualizar_usuario(request, username=None):
    """
    Crea o actualiza un usuario en la base de datos.
    """
    datos = request.POST
    nombre = datos.get("nombre")
    tipo = datos.get("tipo")

    try:
        with transaction.atomic():
            if not username:
                logger.info("Creando un nuevo usuario...")
                with connection.cursor() as cursor:
                    cursor.execute(
                        'INSERT INTO usuario(username, nombre, tipo) VALUES (%s, %s, %s)',
                        [username, nombre, tipo]
                    )
                logger.info("Usuario creado exitosamente.")
            else:
                logger.info(f"Actualizando el usuario con username: {username}...")
                with connection.cursor() as cursor:
                    cursor.execute(
                        'UPDATE usuario SET nombre=%s, tipo=%s WHERE username=%s',
                        [nombre, tipo, username]
                    )
                logger.info("Usuario actualizado exitosamente.")
    except Exception as e:
        logger.error(f"Error al crear/actualizar usuario: {e}")
        return JsonResponse({"error": str(e)}, status=500)

    return redirect("app:gestion_usuario")


def _obtener_usuario(username):
    """
    Obtiene los detalles de un usuario específico utilizando consultas SQL puras.
    """
    if not username:
        return JsonResponse({"error": "Username no proporcionado."}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nombre, tipo, username
                FROM usuario
                WHERE username = %s
            """, [username])
            row = cursor.fetchone()

        if row:
            response_data = {
                "nombre": row[0],
                "tipo": row[1],
                "username": row[2],
            }

            return JsonResponse(response_data)
        else:
            return JsonResponse({"error": "Usuario no encontrado."}, status=404)
    except Exception as e:
        logger.error(f"Error al obtener usuario: {e}")
        return JsonResponse({"error": str(e)}, status=500)


def _eliminar_usuario(username):
    """
    Elimina un usuario de la base de datos.
    """
    if not username:
        return JsonResponse({"error": "Username no proporcionado."}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM usuario WHERE username=%s", [username])
        logger.info(f"Usuario con username {username} eliminado exitosamente.")
        return JsonResponse({"success": "Usuario eliminado"})
    except Exception as e:
        logger.error(f"Error al eliminar usuario: {e}")
        return JsonResponse({"error": str(e)}, status=500)
 
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
    context = {}
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
    # Recuperar lista de estudiantes para el select
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT carnet, nombre FROM alumnos ORDER BY nombre")
            estudiantes = cursor.fetchall()
        context['estudiantes'] = [{'carnet': e[0], 'nombre': e[1]} for e in estudiantes]
    except Exception as e:
        context['error'] = f"No se pudieron cargar los estudiantes. Error: {str(e)}"

    return render(request, "subir_pdf.html", context)




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
