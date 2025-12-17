# posts/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

class PostUpdateMiddleware(MiddlewareMixin):
    """
    Middleware que invalida la caché de posts después de actualizaciones
    """
    
    def process_response(self, request, response):
        # Solo procesar si es una solicitud POST y fue exitosa
        if request.method == 'POST' and response.status_code in [200, 302]:
            # Verificar si fue una actualización de post
            if any(path in request.path for path in ['/editar/', '/actualizar/', '/agregar/']):
                # Invalidar todas las cachés relacionadas con posts
                self.invalidate_post_caches()
        
        return response
    
    def invalidate_post_caches(self):
        """Invalida todas las cachés relacionadas con posts"""
        # Lista de patrones de claves a eliminar
        patterns = [
            'posts_list_',
            'post_details_',
            'categoria_posts_',
            'user_posts_',
        ]
        
        deleted_count = 0
        # Nota: Esto depende de tu backend de caché
        # Para Redis, podrías usar: cache.delete_pattern('posts_*')
        
        # Para cache local de Django
        if hasattr(cache, '_cache'):
            keys_to_delete = []
            for key in cache._cache.keys():
                if any(pattern in key for pattern in patterns):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                cache.delete(key)
                deleted_count += 1
        
        return deleted_count