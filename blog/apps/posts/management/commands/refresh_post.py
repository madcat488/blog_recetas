from django.core.management.base import BaseCommand
from django.core.cache import cache
from posts.models import Post

class Command(BaseCommand):
    help = 'Refresca todos los posts desde la base de datos y limpia caché'
    
    def handle(self, *args, **options):
        self.stdout.write('Refrescando posts...')
        
        # 1. Refrescar todos los posts
        posts = Post.objects.all()
        for post in posts:
            post.refresh_from_db()
        
        self.stdout.write(f'Refrescados {posts.count()} posts')
        
        # 2. Limpiar caché de posts
        cache_keys_to_delete = []
        for key in cache._cache.keys():
            if key.startswith('post_') or key.startswith('posts_'):
                cache_keys_to_delete.append(key)
        
        for key in cache_keys_to_delete:
            cache.delete(key)
        
        self.stdout.write(f'Eliminadas {len(cache_keys_to_delete)} claves de caché')
        self.stdout.write(self.style.SUCCESS('¡Posts refrescados exitosamente!'))