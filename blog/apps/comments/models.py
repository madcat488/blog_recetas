from django.db import models

from apps.usuarios.models import Usuario
from apps.post.models import Post

# Create your models here.
class Comentario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    autor = models.CharField(max_length=100)
    contenido = models.TextField(verbose_name='Contenido del comentario')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comentario de {self.autor} en {self.post.titulo}'  
    
    class Meta:
        ordering = ['-fecha_creacion']