from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.generic import CreateView, View
from django.contrib.auth.views import LoginView as AuthLoginView
from django.urls import reverse, reverse_lazy
from .forms import EditarPerfilForm, RegistroForm, RegistroUsuarioForm, CustomPasswordChangeForm
from .models import Usuario
from apps.posts.models import Post 
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView, FormView
from django.contrib.auth import update_session_auth_hash

# ============== VISTAS DE AUTENTICACIÓN ==============

class RegistrarUsuario(CreateView):
    model = Usuario
    form_class = RegistroForm  # Cambié de 'form' a 'form_class'
    template_name = 'usuarios/registrar.html'
    success_url = reverse_lazy('index')

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Inicia sesión automáticamente después del registro
            messages.success(request, '¡Registro exitoso! Bienvenido/a a nuestra comunidad viajera.')
            return redirect('nombre_de_la_url_de_inicio')  # Cambia esto por tu URL de inicio
        else:
            messages.error(request, 'Por favor, corrige los errores del formulario.')
    else:
        form = RegistroForm()
    
    return render(request, 'usuarios/registrar.html', {'form': form})

class LoginView(AuthLoginView):
    template_name = 'usuarios/login.html'
    
    def form_valid(self, form):
        messages.success(self.request, f'¡Bienvenido {form.get_user().username}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Usuario o contraseña incorrectos.')
        return super().form_invalid(form)

class CerrarSesionView(View):
    def get(self, request):
        logout(request)
        messages.success(request, '¡Has cerrado sesión exitosamente!')
        return redirect('index')

# ============== VISTAS DE PERFIL ==============

class PerfilUsuario(LoginRequiredMixin, View):
    template_name = 'usuarios/perfil.html'
    
    def get(self, request, *args, **kwargs):
        posts_count = Post.objects.filter(autor=request.user).count()
        ultimos_posts = Post.objects.filter(autor=request.user).order_by('-fecha_publicacion')[:5]
        
        context = {
            'user': request.user,
            'posts_count': posts_count,
            'ultimos_posts': ultimos_posts,
            'comentarios_count': 0,
        }
        return render(request, self.template_name, context)

class EditarPerfil(LoginRequiredMixin, UpdateView):
    form_class = EditarPerfilForm
    template_name = 'usuarios/editar_perfil.html'
    success_url = reverse_lazy('usuarios:perfil')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '¡Perfil actualizado correctamente!')
        return HttpResponseRedirect(reverse('usuarios:editar_exitoso'))

class CambiarPassword(LoginRequiredMixin, FormView):
    form_class = CustomPasswordChangeForm
    template_name = 'usuarios/cambiar_password.html'
    success_url = reverse_lazy('usuarios:perfil')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, '¡Contraseña actualizada exitosamente!')
        return HttpResponseRedirect(reverse('usuarios:cambio_password_exitoso'))

# ============== VISTAS DE ÉXITO ==============

def editar_exitoso(request):
    return render(request, 'usuarios/editar_exitoso.html')

def cambio_password_exitoso(request):
    return render(request, 'usuarios/cambio_password_exitoso.html')