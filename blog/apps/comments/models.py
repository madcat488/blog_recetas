from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.posts.models import Post

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
    
    # CORRECCIÓN: Quitar @property y dejar como método normal
    def puede_ser_moderado_por(self, user):
        """
        Verifica si un usuario puede moderar este comentario.
        """
        if not user.is_authenticated:
            return False
        
        # Superusuarios y staff pueden moderar todo
        if user.is_superuser or user.is_staff:
            return True
        
        # Colaboradores pueden moderar comentarios en sus propios posts
        if hasattr(user, 'colaborador') and user.colaborador:
            if self.post.autor == user:
                return True
        
        return False
    
    def puede_ser_editado_por(self, user):
        """
        Verifica si un usuario puede editar este comentario.
        Solo el autor puede editar su propio comentario.
        """
        return user.is_authenticated and user == self.usuario
    
    def puede_ser_eliminado_por(self, user):
        """
        Verifica si un usuario puede eliminar este comentario.
        """
        if not user.is_authenticated:
            return False
        
        # El autor puede eliminar su propio comentario
        if user == self.usuario:
            return True
        
        # Moderadores pueden eliminar
        return self.puede_ser_moderado_por(user)
    
    def get_estado_display_class(self):
        """
        Devuelve la clase CSS para el estado.
        """
        estado_classes = {
            'pendiente': 'warning',
            'aprobado': 'success',
            'rechazado': 'danger'
        }
        return estado_classes.get(self.estado, 'secondary')
    
    @property
    def esta_aprobado(self):
        """Propiedad para verificar si está aprobado"""
        return self.estado == 'aprobado'
    
    @property
    def esta_pendiente(self):
        """Propiedad para verificar si está pendiente"""
        return self.estado == 'pendiente'
    
    @property
    def esta_rechazado(self):
        """Propiedad para verificar si está rechazado"""
        return self.estado == 'rechazado'
    
    @property
    def aprobado(self):
        """Propiedad para compatibilidad con código antiguo que usa 'aprobado'"""
        return self.estado == 'aprobado'
    
    def aprobar(self, moderador=None):
        """Aprueba el comentario"""
        self.estado = 'aprobado'
        self.moderado_por = moderador
        self.fecha_moderacion = timezone.now()
        self.save()
    
    def rechazar(self, moderador=None, motivo=""):
        """Rechaza el comentario"""
        self.estado = 'rechazado'
        self.moderado_por = moderador
        self.motivo_rechazo = motivo
        self.fecha_moderacion = timezone.now()
        self.save()
    
    def marcar_como_pendiente(self):
        """Marca el comentario como pendiente"""
        self.estado = 'pendiente'
        self.moderado_por = None
        self.motivo_rechazo = ""
        self.fecha_moderacion = None
        self.save()
    
    @property
    def tiempo_transcurrido(self):
        """
        Devuelve el tiempo transcurrido desde la creación.
        """
        delta = timezone.now() - self.fecha_creacion
        
        if delta.days > 365:
            años = delta.days // 365
            return f'hace {años} año{"s" if años > 1 else ""}'
        elif delta.days > 30:
            meses = delta.days // 30
            return f'hace {meses} mes{"es" if meses > 1 else ""}'
        elif delta.days > 0:
            return f'hace {delta.days} día{"s" if delta.days > 1 else ""}'
        elif delta.seconds > 3600:
            horas = delta.seconds // 3600
            return f'hace {horas} hora{"s" if horas > 1 else ""}'
        elif delta.seconds > 60:
            minutos = delta.seconds // 60
            return f'hace {minutos} minuto{"s" if minutos > 1 else ""}'
        else:
            return 'hace unos segundos'
    
    class Meta:
        ordering = ['-fecha_creacion']
        permissions = [
            ("moderar_comentarios", "Puede moderar comentarios de otros usuarios"),
            ("ver_comentarios_pendientes", "Puede ver comentarios pendientes"),
        ]
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'


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
        verbose_name = 'Reacción'
        verbose_name_plural = 'Reacciones'
    
    def __str__(self):
        return f'{self.usuario.username} - {self.get_tipo_display()} en comentario #{self.comentario.id}'