from django.db import models

# Create your models here.
class Categoria(models.Model):
    nombre = models.CharField(max_length=50, null=False, unique=True)
    
    def __str__(self):
        return self.nombre
    
class Post(models.Model):
    titulo = models.CharField(max_length=100, null=False)
    contenido = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    imagen = models.ImageField(upload_to='posts', null=True, blank=True, default='posts/default_post.png')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='posts')
    
    def __str__(self):
        return self.titulo