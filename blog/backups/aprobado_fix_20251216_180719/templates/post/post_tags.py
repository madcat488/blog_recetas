from django import template
from ..models import Post
from django.db.models import Q

register = template.Library()

@register.simple_tag
def get_recent_posts(count=5):
    """Obtiene los posts más recientes publicados"""
    return Post.objects.filter(
        estado='publicado',
        visibilidad='publico'
    ).order_by('-fecha_creacion')[:count]

@register.simple_tag
def get_popular_posts(count=5):
    """Obtiene los posts más vistos"""
    return Post.objects.filter(
        estado='publicado',
        visibilidad='publico'
    ).order_by('-vistas')[:count]