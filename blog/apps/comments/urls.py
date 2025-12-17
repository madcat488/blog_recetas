# apps/comments/urls.py
from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    # URLs para usuarios normales
    path('agregar/<int:post_id>/', views.agregar_comentario, name='agregar_comentario'),
    path('editar/<int:comentario_id>/', views.editar_comentario, name='editar_comentario'),
    path('eliminar/<int:comentario_id>/', views.eliminar_comentario, name='eliminar_comentario'),
    
    # URLs para moderación
    path('pendientes/', views.comentarios_pendientes, name='comentarios_pendientes'),
    path('moderar/<int:comentario_id>/', views.moderar_comentario, name='moderar_comentario'),
    path('aprobar-rapido/<int:comentario_id>/', views.aprobar_comentario_rapido, name='aprobar_comentario_rapido'),
    path('rechazar-rapido/<int:comentario_id>/', views.rechazar_comentario_rapido, name='rechazar_comentario_rapido'),
    
    # URLs para listado (admin)
    path('listar/', views.ListarComentarios.as_view(), name='listar_comentarios'),
    
    # URLs para API/AJAX
    path('api/comentarios/<int:post_id>/', views.api_comentarios, name='api_comentarios'),
    
    # URLs para vistas basadas en clases (mantener compatibilidad)
    path('modificar/<int:pk>/', views.ModificarOpinion.as_view(), name='modificar_comentario'),
    path('eliminar-clase/<int:pk>/', views.EliminarOpinion.as_view(), name='eliminar_comentario_clase'),
]