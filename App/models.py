from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class Usuario(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('alumno', 'Alumno'),
        ('docente', 'Docente'),
        ('administrador', 'Administrador'),
    ]

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    tipo_usuario = models.CharField(max_length=50, choices=TIPO_USUARIO_CHOICES)
    usuario = models.CharField(max_length=100, unique=True)  # Asegura que el usuario sea único
    contrasena = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.tipo_usuario})"

class Curso(models.Model):
    nombre = models.CharField(max_length=100, unique=True)  # Asegura que el nombre del curso sea único

    def __str__(self):
        return self.nombre

class CursoDocente(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    docente = models.ForeignKey('Docente', on_delete=models.CASCADE)  # Referencia a Docente

    class Meta:
        unique_together = ('curso', 'docente')

class Docente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, limit_choices_to={'tipo_usuario': 'docente'})
    cursos = models.ManyToManyField(Curso, through='CursoDocente')

    def __str__(self):
        return f"{self.usuario.nombre} {self.usuario.apellido} (Docente)"

class CursoAlumno(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    alumno = models.ForeignKey('Alumno', on_delete=models.CASCADE)  # Referencia a Alumno

    class Meta:
        unique_together = ('curso', 'alumno')

class Alumno(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, limit_choices_to={'tipo_usuario': 'alumno'})
    cursos = models.ManyToManyField(Curso, through='CursoAlumno')

    def __str__(self):
        return f"{self.usuario.nombre} {self.usuario.apellido} (Alumno)"

class Titulo(models.Model):
    titulo_otorgado = models.CharField(max_length=100, unique=True)  # Asegura que el título sea único
    certificacion_titulo = models.TextField()
    publicacion_gaceta = models.TextField()

    def __str__(self):
        return self.titulo_otorgado

class Certificacion(models.Model):
    certificado_notas = models.TextField()
    acta_culminacion = models.TextField()
    plan_estudios = models.TextField()

    def __str__(self):
        return f"Certificación {self.certificado_notas}"

class Expediente(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    titulo = models.ForeignKey(Titulo, on_delete=models.CASCADE)
    certificacion = models.ForeignKey(Certificacion, on_delete=models.CASCADE)

    def __str__(self):
        return f"Expediente de {self.alumno}"

class Nota(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, null=True)
    nota_por_cuatrimestre = models.DecimalField(max_digits=5, decimal_places=2)
    cuatrimestre = models.CharField(max_length=20)

    def __str__(self):
        return f"Nota de {self.alumno} en {self.cuatrimestre}: {self.nota_por_cuatrimestre}"
