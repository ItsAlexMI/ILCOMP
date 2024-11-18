# Generated by Django 4.2.16 on 2024-11-18 05:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0003_plan_encabezado_delete_alumnos'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alumnos',
            fields=[
                ('carnet', models.IntegerField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=200)),
                ('ano_ingreso', models.IntegerField(default=0)),
                ('username_Alumno', models.CharField(max_length=100, unique=True)),
                ('usernameAlumno', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'db_table': 'alumnos',
                'managed': False,
            },
        ),
    ]
