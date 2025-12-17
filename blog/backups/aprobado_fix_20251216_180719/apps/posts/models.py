# apps/posts/models.py
from time import timezone
import uuid
from django.db import models
from django.conf import settings  # Importa settings
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify



class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)
    
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(
        upload_to='categorias/',
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        help_text='Imagen representativa de la categoría'
    )
    icono = models.CharField(
        max_length=50, 
        blank=True,
        help_text='Nombre de icono de Bootstrap Icons (ej: bi-globe)'
    )
    color = models.CharField(
        max_length=7,
        default='#6c757d',
        help_text='Color en formato hexadecimal (ej: #6c757d)'
    )
    
    class Meta:
        ordering = ['nombre']
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
    
    def __str__(self):
        return self.nombre
    
    @property
    def tiene_imagen(self):
        """Verifica si la categoría tiene imagen"""
        return bool(self.imagen)

class Post(models.Model):
    # Información básica
    titulo = models.CharField(max_length=200, verbose_name="Título")
    resumen = models.TextField(max_length=300, verbose_name="Descripción corta", help_text="Máximo 300 caracteres. Aparece en las vistas previas.")
    contenido = models.TextField(verbose_name="Contenido completo")
    
    # Multimedia
    imagen = models.ImageField(upload_to='posts/%Y/%m/', verbose_name="Imagen principal", null=True, blank=True)
    
    # Categorización
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, verbose_name="Categoría")
    
    # Información práctica del viaje
    ubicacion_pais = models.CharField(max_length=100, verbose_name="País", blank=True)
    ubicacion_ciudad = models.CharField(max_length=100, verbose_name="Ciudad/Región", blank=True)
    mejor_epoca = models.CharField(max_length=100, verbose_name="Mejor época para visitar", blank=True)
    precio_aproximado = models.CharField(max_length=100, verbose_name="Precio aproximado", blank=True)
    dificultad = models.CharField(
        max_length=20,
        choices=[
            ('facil', 'Fácil'),
            ('moderado', 'Moderado'),
            ('dificil', 'Difícil'),
            ('muy_dificil', 'Muy difícil')
        ],
        blank=True,
        verbose_name="Dificultad"
    )
    duracia_recomendada = models.CharField(max_length=50, verbose_name="Duración recomendada", blank=True)
    cache_version = models.UUIDField(default=uuid.uuid4, editable=False)
    last_cache_invalidation = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Actualizar versión de caché cada vez que se guarda
        self.cache_version = uuid.uuid4()
        self.last_cache_invalidation = timezone.now()
        super().save(*args, **kwargs)
    
    def get_cache_key(self):
        """Genera clave de caché única con versión"""
        return f"post_{self.id}_v{self.cache_version}"
    
    # Control de publicación
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('revision', 'En revisión'),
        ('publicado', 'Publicado'),
        ('archivado', 'Archivado')
    ]
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='borrador',
        verbose_name="Estado"
    )
    
    VISIBILIDAD_CHOICES = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
        ('solo_colaboradores', 'Solo colaboradores')
    ]
    
    visibilidad = models.CharField(
        max_length=20,
        choices=VISIBILIDAD_CHOICES,
        default='publico',
        verbose_name="Visibilidad"
    )
    
    # Metadatos
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    fecha_publicacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de publicación")
    
    # SEO y estadísticas
    palabras_clave = models.CharField(max_length=200, blank=True, verbose_name="Palabras clave")
    vistas = models.PositiveIntegerField(default=0, verbose_name="Número de vistas")
    
    class Meta:
        ordering = ['-fecha_publicacion']
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        permissions = [
            ("can_publish", "Puede publicar posts"),
            ("can_review", "Puede revisar posts"),
        ]
    
    def __str__(self):
        return self.titulo
    
    def save(self, *args, **kwargs):
        # Si se cambia el estado a 'publicado' y no tiene fecha de publicación
        if self.estado == 'publicado' and not self.fecha_publicacion:
            from django.utils import timezone
            self.fecha_publicacion = timezone.now()
        super().save(*args, **kwargs)
    

    @property
    def es_publico(self):
        """Verifica si el post es visible públicamente"""
        return self.estado == 'publicado' and self.visibilidad == 'publico'
    
    @property
    def puede_ver(self, usuario):
        """Determina si un usuario puede ver el post"""
        if self.es_publico:
            return True
        if usuario.is_authenticated:
            if usuario == self.autor:
                return True
            if self.visibilidad == 'solo_colaboradores' and (usuario.colaborador or usuario.is_staff):
                return True
        return False