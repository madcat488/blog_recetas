from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Usuario(AbstractUser):
    nombre = models.CharField(max_length=30, blank=True)
    apellido = models.CharField(max_length=30, blank=True)
    fecha_nacimiento = models.DateField("Fecha Nacimiento",null=True, blank=True, default='2000-01-01')
    email = models.EmailField(unique=True)
    colaborador = models.BooleanField("Colaborador", default=False)
    imagen = models.ImageField(upload_to='usuarios', null=True, blank=True, default='usuarios/default_user.png')
    
    class Meta:
        ordering = ('-nombre',)
        
    def __str__(self):
        return self.nombre
    