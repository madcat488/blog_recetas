from django import template
from django.core.cache import cache
from django.utils import timezone
from django.utils.timesince import timesince

register = template.Library()

# NO importes el modelo aquí directamente
# Django lo resolverá cuando sea necesario

@register.filter
def force_refresh(post):
    """
    Filtro que fuerza la actualización de un post desde la base de datos.
    """
    if post and hasattr(post, 'refresh_from_db'):
        try:
            post.refresh_from_db()
            return post
        except Exception:
            return post
    return post

@register.simple_tag(takes_context=True)
def get_fresh_post(context, post_id):
    """
    Tag que obtiene un post fresco desde la base de datos.
    """
    # Importa el modelo DENTRO de la función para evitar problemas
    try:
        from apps.posts.models import Post
        post = Post.objects.get(id=post_id)
        post.refresh_from_db()
        return post
    except Exception:
        return None

@register.simple_tag
def invalidate_post_cache(post_id):
    """
    Invalida la caché para un post específico.
    """
    cache_keys = [
        f'post_{post_id}_details',
        f'post_{post_id}_cached',
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    return ''

@register.simple_tag
def is_post_stale(post, threshold_seconds=30):
    """
    Verifica si un post está "desactualizado".
    """
    if not post or not hasattr(post, 'fecha_actualizacion'):
        return True
    
    now = timezone.now()
    delta = now - post.fecha_actualizacion
    
    return delta.total_seconds() > threshold_seconds

@register.filter
def format_updated_time(post):
    """
    Formatea el tiempo desde la última actualización.
    """
    if not post or not hasattr(post, 'fecha_actualizacion'):
        return "Desconocido"
    
    now = timezone.now()
    
    if (now - post.fecha_actualizacion).total_seconds() < 60:
        return "Recién actualizado"
    else:
        return f"Hace {timesince(post.fecha_actualizacion, now)}"

@register.inclusion_tag('posts/partials/refresh_badge.html')
def refresh_badge(post):
    """
    Tag de inclusión que muestra un badge.
    """
    is_stale = False
    if post and hasattr(post, 'fecha_actualizacion'):
        threshold = 300  # 5 minutos
        is_stale = (timezone.now() - post.fecha_actualizacion).total_seconds() > threshold
    
    return {
        'post': post,
        'is_stale': is_stale,
        'post_id': post.id if post else None,
    }

# Filtros simples sin imports problemáticos
@register.filter
def truncate_words(value, num_words=20):
    """Trunca un texto a un número específico de palabras."""
    if not value:
        return ''
    words = str(value).split()
    if len(words) > num_words:
        return ' '.join(words[:num_words]) + '...'
    return value

@register.filter
def format_date(value, format_string='d M Y'):
    """Formatea una fecha."""
    if not value:
        return ''
    return value.strftime(format_string)

@register.filter
def get_item(dictionary, key):
    """Obtiene un item de un diccionario."""
    return dictionary.get(key, '')