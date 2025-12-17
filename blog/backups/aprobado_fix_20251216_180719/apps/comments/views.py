# apps/comments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Comentario
from .forms import ComentarioForm, ModerarComentarioForm
from apps.posts.models import Post

# ========== DECORADORES DE PERMISOS ==========

def puede_moderar_comentarios(user):
    """Verifica si el usuario puede moderar comentarios"""
    return user.is_authenticated and (
        user.is_superuser or 
        user.is_staff or 
        user.colaborador
    )

def puede_ver_pendientes(user):
    """Verifica si el usuario puede ver comentarios pendientes"""
    return user.is_authenticated and (
        user.is_superuser or 
        user.is_staff or 
        user.has_perm('comments.ver_comentarios_pendientes')
    )

# ========== VISTAS DE USUARIO ==========

@login_required
def agregar_comentario(request, post_id):
    """Agrega un comentario a un post específico"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.post = post
            comentario.usuario = request.user
            comentario.autor = request.user.username
            
            # Colaboradores y staff tienen comentarios auto-aprobados en sus propios posts
            if (request.user.colaborador or request.user.is_staff) and post.autor == request.user:
                comentario.estado = 'aprobado'
                comentario.moderado_por = request.user
                comentario.fecha_moderacion = timezone.now()
                mensaje = '¡Comentario publicado!'
            else:
                comentario.estado = 'pendiente'
                mensaje = '¡Comentario enviado! Será revisado por un moderador antes de publicarse.'
            
            comentario.save()
            
            # Si es AJAX, devolver JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': mensaje,
                    'estado': comentario.estado,
                    'comentario_id': comentario.id,
                    'auto_aprobado': comentario.estado == 'aprobado'
                })
            
            messages.success(request, mensaje)
            return redirect('posts:detalle_post', pk=post_id)
    
    messages.error(request, 'Error al publicar el comentario.')
    return redirect('posts:detalle_post', pk=post_id)

@login_required
def editar_comentario(request, comentario_id):
    """Edita un comentario existente"""
    comentario = get_object_or_404(Comentario, id=comentario_id)
    
    # Verificar permisos - solo el autor puede editar
    if comentario.usuario != request.user:
        messages.error(request, 'No tienes permiso para editar este comentario.')
        return redirect('posts:detalle_post', pk=comentario.post.id)
    
    # Si está aprobado, al editar vuelve a pendiente
    if comentario.estado == 'aprobado':
        comentario.estado = 'pendiente'
        comentario.save(update_fields=['estado'])
    
    if request.method == 'POST':
        form = ComentarioForm(request.POST, instance=comentario)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Comentario actualizado! Será revisado nuevamente.')
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Comentario actualizado y enviado para revisión'
                })
    
    return redirect('posts:detalle_post', pk=comentario.post.id)

@login_required
def eliminar_comentario(request, comentario_id):
    """Elimina un comentario"""
    comentario = get_object_or_404(Comentario, id=comentario_id)
    post_id = comentario.post.id
    
    # Verificar permisos - autor o moderadores
    puede_eliminar = (
        comentario.usuario == request.user or
        request.user.is_staff or
        request.user.is_superuser or
        (request.user.colaborador and comentario.post.autor == request.user)
    )
    
    if not puede_eliminar:
        messages.error(request, 'No tienes permiso para eliminar este comentario.')
        return redirect('posts:detalle_post', pk=post_id)
    
    comentario.delete()
    messages.success(request, 'Comentario eliminado.')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Comentario eliminado'
        })
    
    return redirect('posts:detalle_post', pk=post_id)

# ========== VISTAS DE MODERACIÓN ==========

@login_required
@user_passes_test(puede_moderar_comentarios)
def moderar_comentario(request, comentario_id):
    """Vista para moderar un comentario específico"""
    comentario = get_object_or_404(Comentario, id=comentario_id)
    
    # Verificar permisos específicos
    if not comentario.puede_ser_moderado_por(request.user):
        messages.error(request, 'No tienes permiso para moderar este comentario.')
        return redirect('posts:detalle_post', pk=comentario.post.id)
    
    if request.method == 'POST':
        form = ModerarComentarioForm(request.POST, instance=comentario, user=request.user)
        if form.is_valid():
            comentario_moderado = form.save(commit=False)
            comentario_moderado.moderado_por = request.user
            comentario_moderado.fecha_moderacion = timezone.now()
            comentario_moderado.save()
            
            messages.success(request, f'Comentario {comentario_moderado.get_estado_display()}')
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'estado': comentario_moderado.estado,
                    'estado_display': comentario_moderado.get_estado_display(),
                    'moderado_por': request.user.username
                })
            
            return redirect('comments:comentarios_pendientes')
    
    else:
        form = ModerarComentarioForm(instance=comentario, user=request.user)
    
    context = {
        'comentario': comentario,
        'form': form,
        'es_moderador': True,
    }
    
    return render(request, 'comments/moderar_comentario.html', context)

@login_required
@user_passes_test(puede_ver_pendientes)
def comentarios_pendientes(request):
    """Lista de comentarios pendientes de moderación"""
    # Base queryset
    comentarios = Comentario.objects.filter(estado='pendiente')
    
    # Filtrar según permisos
    if not (request.user.is_superuser or request.user.is_staff):
        # Colaboradores solo ven comentarios de sus propios posts
        comentarios = comentarios.filter(post__autor=request.user)
    
    # Ordenar
    comentarios = comentarios.order_by('fecha_creacion')
    
    # Estadísticas
    total_pendientes = comentarios.count()
    total_aprobados = Comentario.objects.filter(estado='aprobado').count()
    total_rechazados = Comentario.objects.filter(estado='rechazado').count()
    
    # Paginación
    paginator = Paginator(comentarios, 20)
    page = request.GET.get('page')
    comentarios_paginados = paginator.get_page(page)
    
    context = {
        'comentarios': comentarios_paginados,
        'total_pendientes': total_pendientes,
        'total_aprobados': total_aprobados,
        'total_rechazados': total_rechazados,
        'es_moderador': True,
    }
    
    return render(request, 'comments/pendientes.html', context)

@login_required
@user_passes_test(puede_moderar_comentarios)
def aprobar_comentario_rapido(request, comentario_id):
    """Aprobar un comentario rápidamente (para AJAX)"""
    comentario = get_object_or_404(Comentario, id=comentario_id)
    
    if not comentario.puede_ser_moderado_por(request.user):
        return JsonResponse({
            'success': False,
            'error': 'No tienes permiso para moderar este comentario'
        }, status=403)
    
    comentario.estado = 'aprobado'
    comentario.moderado_por = request.user
    comentario.fecha_moderacion = timezone.now()
    comentario.save()
    
    return JsonResponse({
        'success': True,
        'estado': 'aprobado',
        'estado_display': 'Aprobado',
        'moderado_por': request.user.username
    })

@login_required
@user_passes_test(puede_moderar_comentarios)
def rechazar_comentario_rapido(request, comentario_id):
    """Rechazar un comentario rápidamente (para AJAX)"""
    comentario = get_object_or_404(Comentario, id=comentario_id)
    
    if not comentario.puede_ser_moderado_por(request.user):
        return JsonResponse({
            'success': False,
            'error': 'No tienes permiso para moderar este comentario'
        }, status=403)
    
    comentario.estado = 'rechazado'
    comentario.moderado_por = request.user
    comentario.fecha_moderacion = timezone.now()
    comentario.save()
    
    return JsonResponse({
        'success': True,
        'estado': 'rechazado',
        'estado_display': 'Rechazado',
        'moderado_por': request.user.username
    })

# ========== VISTAS DE API/AJAX ==========

def api_comentarios(request, post_id):
    """API para obtener comentarios de un post (para AJAX)"""
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    
    # Determinar qué comentarios puede ver el usuario
    comentarios_qs = post.comentarios.all()
    
    # Usuarios no autenticados solo ven aprobados
    if not user.is_authenticated:
        comentarios_qs = comentarios_qs.filter(estado='aprobado')
    
    # Usuarios autenticados normales ven aprobados y sus propios pendientes/rechazados
    elif not (user.is_staff or user.is_superuser or user.colaborador):
        comentarios_qs = comentarios_qs.filter(
            Q(estado='aprobado') |
            Q(estado='pendiente', usuario=user) |
            Q(estado='rechazado', usuario=user)
        )
    
    # Staff, superusuarios y colaboradores (en sus propios posts) ven todo
    elif user.colaborador and not (user.is_staff or user.is_superuser):
        # Colaboradores ven todo en sus posts, solo aprobados en otros
        if post.autor == user:
            comentarios_qs = comentarios_qs.all()  # Ven todo en sus posts
        else:
            comentarios_qs = comentarios_qs.filter(estado='aprobado')
    else:
        # Staff y superusuarios ven todo
        comentarios_qs = comentarios_qs.all()
    
    comentarios = comentarios_qs.order_by('-fecha_creacion')
    
    data = []
    for comentario in comentarios:
        puede_moderar = comentario.puede_ser_moderado_por(user)
        
        data.append({
            'id': comentario.id,
            'autor': comentario.autor,
            'contenido': comentario.contenido,
            'fecha_creacion': comentario.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'fecha_creacion_iso': comentario.fecha_creacion.isoformat(),
            'me_gusta': comentario.me_gusta,
            'estado': comentario.estado,
            'estado_display': comentario.get_estado_display(),
            'usuario_id': comentario.usuario.id,
            'puede_editar': user.is_authenticated and user == comentario.usuario,
            'puede_eliminar': user.is_authenticated and (
                user == comentario.usuario or 
                user.is_staff or 
                user.is_superuser or
                (user.colaborador and post.autor == user)
            ),
            'puede_moderar': puede_moderar,
            'es_mio': user.is_authenticated and user == comentario.usuario,
            'moderado_por': comentario.moderado_por.username if comentario.moderado_por else None,
            'fecha_moderacion': comentario.fecha_moderacion.isoformat() if comentario.fecha_moderacion else None,
        })
    
    return JsonResponse({
        'comentarios': data,
        'total': len(data),
        'post': {
            'id': post.id,
            'titulo': post.titulo,
            'autor_id': post.autor.id,
        },
        'usuario': {
            'id': user.id if user.is_authenticated else None,
            'es_staff': user.is_staff if user.is_authenticated else False,
            'es_superuser': user.is_superuser if user.is_authenticated else False,
            'es_colaborador': user.colaborador if user.is_authenticated else False,
            'es_autor_post': user.is_authenticated and user == post.autor,
        }
    })

# ========== VISTAS BASADAS EN CLASES ==========

class ModificarOpinion(LoginRequiredMixin, UpdateView):
    model = Comentario
    form_class = ComentarioForm
    template_name = 'comments/editar_comentario.html'
    
    def get_success_url(self):
        return reverse_lazy('posts:detalle_post', kwargs={'pk': self.object.post.id})
    
    def test_func(self):
        comentario = self.get_object()
        return self.request.user == comentario.usuario

class EliminarOpinion(LoginRequiredMixin, DeleteView):
    model = Comentario
    template_name = 'comments/eliminar_comentario.html'
    
    def get_success_url(self):
        return reverse_lazy('posts:detalle_post', kwargs={'pk': self.object.post.id})
    
    def test_func(self):
        comentario = self.get_object()
        user = self.request.user
        return (
            user == comentario.usuario or
            user.is_staff or
            user.is_superuser or
            (user.colaborador and comentario.post.autor == user)
        )

class ListarComentarios(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Comentario
    template_name = 'comments/listar_comentarios.html'
    context_object_name = 'comentarios'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        autor = self.request.GET.get('autor')
        if autor:
            queryset = queryset.filter(autor__icontains=autor)
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = Comentario.ESTADO_CHOICES
        return context