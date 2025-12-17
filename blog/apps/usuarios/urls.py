
from django.urls import path

from apps.usuarios import views


app_name = 'usuarios'

urlpatterns = [
    # URLs de autenticación
    path('registrar/', views.RegistrarUsuario.as_view(), name='registrar'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.CerrarSesionView.as_view(), name='cerrar_sesion'),
    
    # URLs de perfil
    path('perfil/', views.PerfilUsuario.as_view(), name='perfil'),
    path('perfil/editar/', views.EditarPerfil.as_view(), name='editar_perfil'),
    path('perfil/cambiar-password/', views.CambiarPassword.as_view(), name='cambiar_password'),
]