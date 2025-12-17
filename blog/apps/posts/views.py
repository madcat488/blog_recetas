# apps/posts/views.py
from urllib import request
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from .models import Categoria, Post
from .forms import CategoriaForm, PostForm
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.views.generic import TemplateView
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from apps.usuarios.templatetags.user_tags import puede_crear_post
from django.utils import timezone

# ========== VISTAS BASADAS EN CLASES ==========

class AgregarCategoria(LoginRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'post/agregar_categoria.html'
    success_url = reverse_lazy('posts:listar_posts')
    login_url = '/login/'
    
    def form_valid(self, form):
        messages.success(self.request, '¡Categoría creada exitosamente!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        return context

class ActualizarCategoria(LoginRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'post/agregar_categoria.html'
    success_url = reverse_lazy('posts:listar_posts')
    login_url = '/login/'
    
    def form_valid(self, form):
        messages.success(self.request, '¡Categoría actualizada exitosamente!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        return context

class EliminarCategoria(LoginRequiredMixin, DeleteView):
    model = Categoria
    template_name = 'post/confirmar_eliminar_categoria.html'
    success_url = reverse_lazy('posts:listar_posts')
    login_url = '/login/'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Categoría eliminada exitosamente')
        return super().delete(request, *args, **kwargs)

class AgregarPost(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'post/agregar_post.html'
    
    def test_func(self):
        return self.request.user.colaborador or self.request.user.is_staff or self.request.user.is_superuser
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.autor = self.request.user
        response = super().form_valid(form)
        
        estado = form.cleaned_data.get('estado')
        if estado == 'publicado':
            messages.success(self.request, '¡Publicación creada y publicada correctamente!')
        elif estado == 'revision':
            messages.info(self.request, '¡Publicación enviada a revisión!')
        else:
            messages.success(self.request, '¡Borrador guardado correctamente!')
        
        return response
    
    def get_success_url(self):
        return reverse_lazy('posts:detalle_post', kwargs={'pk': self.object.pk})

class ActualizarPost(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'post/editar_post.html'
    context_object_name = 'post'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.refresh_from_db()
        messages.success(self.request, '¡Cambios realizados correctamente!')
        
        if 'seguir_editando' in self.request.POST:
            return HttpResponseRedirect(
                reverse('posts:actualizar_post', kwargs={'pk': self.object.pk})
            )
        elif 'ver_publicacion' in self.request.POST:
            return HttpResponseRedirect(
                reverse('posts:detalle_post', kwargs={'pk': self.object.pk})
            )
        else:
            return HttpResponseRedirect(
                reverse('posts:editar_exitoso', kwargs={'pk': self.object.pk})
            )

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.autor or self.request.user.is_staff or self.request.user.is_superuser
    
    def get_success_url(self):
        return reverse_lazy('posts:detalle_post', kwargs={'pk': self.object.pk})
    
class EditarExitoso(TemplateView):
    template_name = 'post/editar_exitoso.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post_id = self.kwargs.get('pk')
        
        try:
            post = Post.objects.get(id=post_id)
            context['post'] = post
        except Post.DoesNotExist:
            pass
        
        storage = messages.get_messages(self.request)
        context['ultimo_mensaje'] = list(storage)[-1] if storage else None
        
        return context

class EliminarPost(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'post/confirma_eliminar.html'
    success_url = reverse_lazy('posts:listar_posts')
    login_url = '/login/'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Viaje eliminado exitosamente')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        return context

class DetallePost(DetailView):
    model = Post
    template_name = 'post/ver_post.html'
    context_object_name = 'post'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        
        # Incrementar vistas - usando F() para evitar race conditions
        Post.objects.filter(id=post.id).update(vistas=F('vistas') + 1)
        post.refresh_from_db()  # Refrescar para obtener el valor actualizado
        
        # Obtener posts relacionados - usando fecha_publicacion
        if post.categoria:
            related_posts = Post.objects.filter(
                categoria=post.categoria,
                estado='publicado',
                visibilidad='publico'
            ).exclude(id=post.id).order_by('-fecha_publicacion')[:3]
            context['related_posts'] = related_posts
        
        # Obtener posts del mismo autor - usando fecha_publicacion
        author_posts = Post.objects.filter(
            autor=post.autor,
            estado='publicado',
            visibilidad='publico'
        ).exclude(id=post.id).order_by('-fecha_publicacion')[:3]
        context['author_posts'] = author_posts
        
        # Obtener comentarios del post - CORREGIDO: usar 'estado' en lugar de 'aprobado'
        try:
            from apps.comments.models import Comentario
            
            # Usuario actual
            user = self.request.user
            
            # Base queryset
            comentarios_qs = post.comentarios.all()
            
            # Determinar qué comentarios puede ver el usuario
            if not user.is_authenticated:
                # Usuarios no autenticados solo ven aprobados
                comentarios_qs = comentarios_qs.filter(estado='aprobado')
            elif not (user.is_staff or user.is_superuser or user.colaborador):
                # Usuarios normales ven aprobados y sus propios comentarios
                comentarios_qs = comentarios_qs.filter(
                    Q(estado='aprobado') |
                    Q(estado='pendiente', usuario=user) |
                    Q(estado='rechazado', usuario=user)
                )
            elif user.colaborador and not (user.is_staff or user.is_superuser):
                # Colaboradores ven todo en sus posts, solo aprobados en otros
                if post.autor == user:
                    # Ven todo en sus propios posts
                    pass  # Mantener todos los comentarios
                else:
                    # Solo aprobados en posts de otros
                    comentarios_qs = comentarios_qs.filter(estado='aprobado')
            # Staff y superusuarios ven todo (no se filtra)
            
            # Ordenar y aplicar paginación
            comentarios = comentarios_qs.order_by('-fecha_creacion')
            
            # Paginación
            paginator = Paginator(comentarios, 10)
            page = self.request.GET.get('page')
            
            try:
                comentarios_paginados = paginator.page(page)
            except PageNotAnInteger:
                comentarios_paginados = paginator.page(1)
            except EmptyPage:
                comentarios_paginados = paginator.page(paginator.num_pages)
            
            context['comentarios'] = comentarios_paginados
            
            # Agregar formulario de comentarios si está disponible
            try:
                from apps.comments.forms import ComentarioForm
                context['comentario_form'] = ComentarioForm()
            except ImportError:
                pass
                
        except ImportError:
            # Si no se puede importar el modelo de comentarios, simplemente no los agregamos
            context['comentarios'] = []
        
        return context

class ListarPost(ListView):
    model = Post
    template_name = 'post/listar_posts.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    @method_decorator(cache_page(60 * 5))
    @method_decorator(vary_on_cookie)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_queryset(self):
        cache_key = self.get_cache_key()
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        queryset = self.build_queryset()
        cache.set(cache_key, queryset, 60 * 5)
        return queryset
    
    def get_cache_key(self):
        base_key = 'posts_list'
        params = [
            f"user_{self.request.user.id if self.request.user.is_authenticated else 'anon'}",
            f"categoria_{self.request.GET.get('categoria', 'all')}",
            f"buscador_{self.request.GET.get('buscador', 'none')}",
            f"orden_{self.request.GET.get('orden', 'reciente')}",
            f"page_{self.request.GET.get('page', '1')}",
        ]
        return f"{base_key}_{'_'.join(params)}"
    
    def build_queryset(self):
        queryset = Post.objects.all()
        
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                estado='publicado',
                visibilidad='publico'
            )
        elif not (self.request.user.colaborador or self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(
                Q(estado='publicado', visibilidad='publico') |
                Q(estado='borrador', autor=self.request.user) |
                Q(visibilidad='solo_colaboradores') & Q(autor__colaborador=True)
            )
        
        categoria = self.request.GET.get('categoria')
        if categoria and categoria != 'all':
            queryset = queryset.filter(categoria__nombre=categoria)
        
        buscador = self.request.GET.get('buscador')
        if buscador:
            queryset = queryset.filter(
                Q(titulo__icontains=buscador) | 
                Q(contenido__icontains=buscador) |
                Q(resumen__icontains=buscador) |
                Q(autor__username__icontains=buscador)
            )
        
        orden = self.request.GET.get('orden', 'reciente')
        if orden == 'antiguo':
            queryset = queryset.order_by('fecha_publicacion')
        elif orden == 'titulo':
            queryset = queryset.order_by('titulo')
        else:
            queryset = queryset.order_by('-fecha_publicacion')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.GET.get('refresh') == 'true':
            cache_key = self.get_cache_key()
            cache.delete(cache_key)
        
        return context

class MisPublicaciones(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'post/mis_publicaciones.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Post.objects.filter(autor=self.request.user)
        
        estado = self.request.GET.get('estado')
        if estado and estado in ['borrador', 'revision', 'publicado', 'archivado']:
            queryset = queryset.filter(estado=estado)
        
        visibilidad = self.request.GET.get('visibilidad')
        if visibilidad and visibilidad in ['publico', 'privado', 'solo_colaboradores']:
            queryset = queryset.filter(visibilidad=visibilidad)
        
        busqueda = self.request.GET.get('busqueda')
        if busqueda:
            queryset = queryset.filter(
                Q(titulo__icontains=busqueda) | 
                Q(contenido__icontains=busqueda) |
                Q(resumen__icontains=busqueda) |
                Q(palabras_clave__icontains=busqueda) |
                Q(ubicacion_pais__icontains=busqueda) |
                Q(ubicacion_ciudad__icontains=busqueda)
            )
        
        orden = self.request.GET.get('orden', 'reciente')
        if orden == 'antiguo':
            queryset = queryset.order_by('fecha_publicacion')
        elif orden == 'titulo':
            queryset = queryset.order_by('titulo')
        else:
            queryset = queryset.order_by('-fecha_publicacion')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts_usuario = Post.objects.filter(autor=self.request.user)
        
        context.update({
            'total_publicaciones': posts_usuario.count(),
            'publicados': posts_usuario.filter(estado='publicado').count(),
            'borradores': posts_usuario.filter(estado='borrador').count(),
            'en_revision': posts_usuario.filter(estado='revision').count(),
            'archivados': posts_usuario.filter(estado='archivado').count(),
            'publicos': posts_usuario.filter(visibilidad='publico').count(),
            'privados': posts_usuario.filter(visibilidad='privado').count(),
            'solo_colaboradores': posts_usuario.filter(visibilidad='solo_colaboradores').count(),
            'categorias_usuario': posts_usuario.values('categoria__nombre').annotate(
                total=Count('id')
            ).order_by('-total'),
        })
        
        return context

# ========== VISTAS BASADAS EN FUNCIONES ==========

def listar_por_categoria(request, categoria):
    """
    Vista para listar posts por categoría.
    PARÁMETRO CORREGIDO: 'categoria' en lugar de 'categoria_nombre'
    """
    # Limpiar el nombre de la categoría
    categoria_nombre = str(categoria).strip()
    
    # SOLUCIÓN AL ERROR: Manejar múltiples categorías con el mismo nombre
    try:
        # Primero intenta obtener una sola categoría (insensible a mayúsculas)
        categoria_obj = Categoria.objects.get(nombre__iexact=categoria_nombre)
    except Categoria.MultipleObjectsReturned:
        # Si hay múltiples categorías con el mismo nombre, toma la primera
        categoria_obj = Categoria.objects.filter(nombre__iexact=categoria_nombre).first()
        # Opcional: mostrar advertencia en debug
        if request.user.is_staff:
            messages.warning(request, f'Advertencia: Existen múltiples categorías con el nombre "{categoria_nombre}". Se muestra la primera.')
    except Categoria.DoesNotExist:
        # Si la categoría no existe, intentar buscar por slug
        try:
            # Convertir a slug y buscar
            from django.utils.text import slugify
            slug = slugify(categoria_nombre)
            categoria_obj = Categoria.objects.get(slug=slug)
        except Categoria.DoesNotExist:
            # Si la categoría no existe, muestra página de categoría vacía
            return render(request, 'post/empty_category.html', {
                'categoria_nombre': categoria_nombre,
                'total_categorias': Categoria.objects.count(),
                'total_posts': Post.objects.filter(estado='publicado').count(),
                'otras_categorias': Categoria.objects.annotate(
                    post_count=Count('post', filter=Q(post__estado='publicado'))
                ).filter(post_count__gt=0).order_by('-post_count')[:10],
            })
    
    # Base queryset
    posts = Post.objects.filter(categoria=categoria_obj)
    
    # Filtrar por estado según usuario
    if not request.user.is_authenticated:
        posts = posts.filter(
            estado='publicado',
            visibilidad='publico'
        )
    elif not (request.user.colaborador or request.user.is_staff or request.user.is_superuser):
        posts = posts.filter(
            Q(estado='publicado', visibilidad='publico') |
            Q(estado='borrador', autor=request.user) |
            Q(visibilidad='solo_colaboradores') & Q(autor__colaborador=True)
        )
    else:
        posts = posts.filter(
            Q(visibilidad='publico') |
            Q(visibilidad='solo_colaboradores') |
            Q(autor=request.user)
        )
    
    # Orden
    orden = request.GET.get('orden', 'reciente')
    if orden == 'antiguo':
        posts = posts.order_by('fecha_publicacion')
    elif orden == 'titulo':
        posts = posts.order_by('titulo')
    elif orden == 'popular':
        posts = posts.order_by('-vistas')
    else:
        posts = posts.order_by('-fecha_publicacion')
    
    # Búsqueda
    buscador = request.GET.get('buscador')
    if buscador:
        posts = posts.filter(
            Q(titulo__icontains=buscador) | 
            Q(contenido__icontains=buscador) |
            Q(resumen__icontains=buscador) |
            Q(autor__username__icontains=buscador)
        )
    
    # Paginación
    paginator = Paginator(posts, 9)
    page = request.GET.get('page')
    try:
        posts_paginados = paginator.page(page)
    except PageNotAnInteger:
        posts_paginados = paginator.page(1)
    except EmptyPage:
        posts_paginados = paginator.page(paginator.num_pages)
    
    # Contexto
    context = {
        'categoria': categoria_obj,
        'posts': posts_paginados,
        'posts_count': posts.count(),
        'total_categorias': Categoria.objects.count(),
        'total_posts': Post.objects.filter(estado='publicado').count(),
        'otras_categorias': Categoria.objects.annotate(
            post_count=Count('post', filter=Q(post__estado='publicado'))
        ).exclude(id=categoria_obj.id).filter(post_count__gt=0).order_by('-post_count')[:6],
        'is_paginated': posts_paginados.has_other_pages(),
        'page_obj': posts_paginados,
    }
    
    # Si no hay posts, mostrar template especial
    if not posts.exists():
        return render(request, 'post/empty_category.html', context)
    
    return render(request, 'post/listar_por_categoria.html', context)

@csrf_exempt
@require_POST
@login_required
def api_refresh_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        
        if not (request.user == post.autor or 
                request.user.is_staff or 
                request.user.is_superuser):
            return JsonResponse({
                'success': False,
                'error': 'No tienes permiso para refrescar este post'
            }, status=403)
        
        post.refresh_from_db()
        cache.delete(f'post_{post_id}_details')
        
        return JsonResponse({
            'success': True,
            'message': 'Post refrescado exitosamente',
            'post': {
                'id': post.id,
                'titulo': post.titulo,
                'fecha_actualizacion': post.fecha_actualizacion.isoformat(),
                'vistas': post.vistas
            }
        })
        
    except Post.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Post no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_POST
@login_required
def api_refresh_user_posts(request):
    try:
        posts = Post.objects.filter(autor=request.user)
        refreshed_count = 0
        
        for post in posts:
            post.refresh_from_db()
            refreshed_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Se refrescaron {refreshed_count} posts',
            'refreshed_count': refreshed_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def mis_publicaciones(request):
    """
    Vista para que los colaboradores vean solo sus propias publicaciones.
    """
    # Verificar si el usuario puede crear posts (colaborador, staff o superuser)
    puede_crear = (
        request.user.is_superuser or 
        request.user.is_staff or 
        getattr(request.user, 'colaborador', False)
    )
    
    if not puede_crear:
        # Renderizar template con mensaje de acceso restringido
        return render(request, 'posts/mis_publicaciones.html', {
            'user': request.user,
            'access_denied': True
        })
    
    # Filtrar solo las publicaciones del usuario actual
    publicaciones = Post.objects.filter(autor=request.user)
    
    # Filtrar por estado si se proporciona
    estado_filtro = request.GET.get('estado')
    if estado_filtro:
        publicaciones = publicaciones.filter(estado=estado_filtro)
    
    # Ordenar por fecha de creación (más reciente primero)
    publicaciones = publicaciones.order_by('-fecha_creacion')
    
    # Estadísticas
    total_publicaciones = publicaciones.count()
    publicados_count = publicaciones.filter(estado='publicado').count()
    borradores_count = publicaciones.filter(estado='borrador').count()
    revision_count = publicaciones.filter(estado='revision').count()
    
    # Paginación
    paginator = Paginator(publicaciones, 12)  # 12 posts por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'user': request.user,
        'publicaciones': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'total_publicaciones': total_publicaciones,
        'publicados_count': publicados_count,
        'borradores_count': borradores_count,
        'revision_count': revision_count,
        'estado_filtro': estado_filtro,
    }
    
    return render(request, 'posts/mis_publicaciones.html', context)

@login_required
def listar_mis_posts(request):
    """
    Lista todos los posts del usuario autenticado.
    Diferenciado de mis_publicaciones que es solo para colaboradores.
    """
    # Obtener todos los posts del usuario, independientemente de estado
    posts = Post.objects.filter(autor=request.user)
    
    # Filtrar por estado si se especifica
    estado = request.GET.get('estado')
    if estado:
        posts = posts.filter(estado=estado)
    
    # Ordenar
    posts = posts.order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(posts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_posts': posts.count(),
        'estado': estado,
    }
    
    return render(request, 'posts/mis_posts.html', context)
