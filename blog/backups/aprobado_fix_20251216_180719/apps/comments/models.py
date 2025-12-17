from django.db import models
from django.conf import settings
from apps.posts.models import Post
# Create your models here.
from django.db import models
from django.conf import settings

class Comentario(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='comentarios'
    )
    post = models.ForeignKey(
        'posts.Post', 
        on_delete=models.CASCADE, 
        related_name='comentarios'
    )
    autor = models.CharField(max_length=100)
    contenido = models.TextField(verbose_name='Contenido del comentario')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    me_gusta = models.PositiveIntegerField(default=0)
    
    # Nuevos campos para moderación
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='pendiente',
        verbose_name='Estado de aprobación'
    )
    
    motivo_rechazo = models.TextField(
        blank=True, 
        null=True, 
        verbose_name='Motivo de rechazo (si aplica)'
    )
    
    moderado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comentarios_moderados',
        verbose_name='Moderado por'
    )
    
    fecha_moderacion = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Fecha de moderación'
    )
    
    def __str__(self):
        return f'Comentario de {self.autor} en {self.post.titulo}'  
    
    @property
    def puede_ser_moderado_por(self, user):
        """Determina si un usuario puede moderar este comentario"""
        if not user.is_authenticated:
            return False
        
        # Superusuarios pueden moderar todo
        if user.is_superuser:
            return True
        
        # Staff puede moderar todo
        if user.is_staff:
            return True
        
        # Colaboradores pueden moderar comentarios de sus propios posts
        if user.colaborador and self.post.autor == user:
            return True
        
        return False
    
    @property
    def esta_aprobado(self):
        """Propiedad para verificar si está aprobado"""
        return self.estado == 'aprobado'
    
    class Meta:
        ordering = ['-fecha_creacion']
        permissions = [
            ("moderar_comentarios", "Puede moderar comentarios de otros usuarios"),
            ("ver_comentarios_pendientes", "Puede ver comentarios pendientes"),
        ]

class Reaccion(models.Model):
    TIPO_REACCION = [
        ('like', '👍 Me gusta'),
        ('love', '❤️ Me encanta'),
        ('wow', '😮 Sorprendido'),
        ('sad', '😢 Triste'),
        ('angry', '😡 Enojado'),
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    comentario = models.ForeignKey(
        Comentario, 
        on_delete=models.CASCADE, 
        related_name='reacciones'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_REACCION, default='like')
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['usuario', 'comentario']
        ordering = ['-fecha_publicacion']