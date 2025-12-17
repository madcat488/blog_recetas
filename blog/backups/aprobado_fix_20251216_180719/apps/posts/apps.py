from django.apps import AppConfig


class PostConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.posts'

def ready(self):
        # Esto carga los template tags cuando Django inicia
        import apps.posts.templatetags.posts_extras  # ← Ajusta el nombre