from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.db import models

class docente(models.Model):
    nombre = models.CharField(max_length=200)
    username = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre