from django import template

register = template.Library()

@register.filter
def puede_crear_post(user):
    """
    Verifica si el usuario puede crear posts.
    """
    if not user or not user.is_authenticated:
        return False
    
    # 1. Staff y superusers siempre pueden
    if user.is_staff or user.is_superuser:
        return True
    
    # 2. Verificar atributo 'colaborador'
    if hasattr(user, 'colaborador') and user.colaborador:
        return True
    
    # 3. Verificar por grupos específicos
    try:
        grupos_permitidos = ['Editores', 'Colaboradores']
        for grupo in grupos_permitidos:
            if user.groups.filter(name=grupo).exists():
                return True
    except:
        pass
    
    return False