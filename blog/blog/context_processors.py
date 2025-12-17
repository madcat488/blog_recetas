from apps.posts.models import Categoria

def categorias_globales(request):
    return {
        'categorias': Categoria.objects.all()
    }