from .forms import ComentarioForm

def comentarios_context(request):
    """
    Contexto global para formulario de comentarios.
    Se agrega automáticamente a todos los templates.
    """
    return {
        'comentario_form': ComentarioForm(),
        'puede_comentar': request.user.is_authenticated,
    }