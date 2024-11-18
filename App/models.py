from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.db import models

class docente(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=200)
    username = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = "docente"
        managed=False


class Plan_encabezado(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "plan_encabezado"
        managed = False

class Alumnos(models.Model):
    carnet = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=200)
    ano_ingreso = models.IntegerField(default=0)
    username_Alumno = models.CharField(max_length=100, unique=True)
    id_plan_encabezado = models.ForeignKey(Plan_encabezado,on_delete=models.CASCADE)
    usernameAlumno = models.CharField(max_length=100, unique=True)



    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "alumnos"
        managed = False




