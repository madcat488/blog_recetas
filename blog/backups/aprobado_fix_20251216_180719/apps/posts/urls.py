from django.urls import path
from . import views  # Importa desde la misma app

app_name = 'posts'  # Esto crea el namespace 'posts'

urlpatterns = [
    # Página principal con lista de posts
    path('', views.ListarPost.as_view(), name='listar_posts'),
    
    # Detalle del post - USA 'detalle_post' que ya tienes en tu vista
    path('post/<int:pk>/', views.DetallePost.as_view(), name='detalle_post'),
    
    # Crear nuevo post
    path('agregar/', views.AgregarPost.as_view(), name='agregar_post'),
    
    # Editar post
    path('editar/<int:pk>/', views.ActualizarPost.as_view(), name='actualizar_post'),
    path('editar-exitoso/<int:pk>/', views.EditarExitoso.as_view(), name='editar_exitoso'),
    
    # Eliminar post
    path('eliminar/<int:pk>/', views.EliminarPost.as_view(), name='eliminar_post'),
    
    # Listar posts
    path('', views.ListarPost.as_view(), name='listar_posts'),
    # Categorías
    path('categoria/nueva/', views.AgregarCategoria.as_view(), name='agregar_categoria'),
    path('categoria/editar/<int:pk>/', views.ActualizarCategoria.as_view(), name='actualizar_categoria'),
    path('categoria/eliminar/<int:pk>/', views.EliminarCategoria.as_view(), name='eliminar_categoria'),
    path('categoria/<str:categoria>/', views.listar_por_categoria, name='listar_por_categoria'),
    path('categoria-post/<str:categoria>/', views.listar_por_categoria, name='listar_post_por_categoria'),
    path('mis-publicaciones/', views.MisPublicaciones.as_view(), name='mis_publicaciones'),
    # API para refrescar post
    path('api/posts/<int:post_id>/refresh/', views.api_refresh_post, name='api_refresh_post'),
    path('api/posts/refresh-all/', views.api_refresh_user_posts, name='api_refresh_user_posts'),
]