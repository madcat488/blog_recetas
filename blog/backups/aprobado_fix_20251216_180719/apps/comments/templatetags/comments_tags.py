# apps/comments/templatetags/comments_tags.py
from django import template
from django.db.models import Count
from ..models import Comentario

register = template.Library()

@register.simple_tag
def get_recent_comments(limit=5):
    """Obtiene los comentarios más recientes APROBADOS"""
    return Comentario.objects.filter(
        estado='aprobado'  # ← CAMBIO AQUÍ: 'estado' en lugar de 'aprobado'
    ).select_related('post', 'usuario').order_by('-fecha_creacion')[:limit]

@register.simple_tag
def get_popular_comments(limit=5):
    """Obtiene los comentarios con más 'me gusta' APROBADOS"""
    return Comentario.objects.filter(
        estado='aprobado'  # ← CAMBIO AQUÍ
    ).annotate(
        total_likes=Count('me_gusta')
    ).order_by('-me_gusta')[:limit]

@register.filter
def comentario_count(post):
    """Cuenta los comentarios APROBADOS de un post"""
    return post.comentarios.filter(estado='aprobado').count()  # ← CAMBIO AQUÍ

@register.filter
def has_commented(user, post):
    """Verifica si un usuario ha comentado en un post (cualquier estado)"""
    if not user.is_authenticated:
        return False
    return post.comentarios.filter(usuario=user).exists()

@register.simple_tag
def get_comentarios_pendientes_count(user):
    """Obtiene la cantidad de comentarios pendientes que el usuario puede moderar"""
    if not user.is_authenticated:
        return 0
    
    if user.is_superuser or user.is_staff:
        # Superusuarios y staff ven todos los pendientes
        return Comentario.objects.filter(estado='pendiente').count()
    elif user.colaborador:
        # Colaboradores ven solo pendientes de sus propios posts
        return Comentario.objects.filter(
            estado='pendiente',
            post__autor=user
        ).count()
    
    return 0

@register.filter
def comentarios_por_estado(post, estado):
    """Filtra comentarios por estado"""
    return post.comentarios.filter(estado=estado)

@register.simple_tag
def get_comentarios_estadisticas():
    """Obtiene estadísticas de comentarios"""
    return {
        'total': Comentario.objects.count(),
        'aprobados': Comentario.objects.filter(estado='aprobado').count(),
        'pendientes': Comentario.objects.filter(estado='pendiente').count(),
        'rechazados': Comentario.objects.filter(estado='rechazado').count(),
    }