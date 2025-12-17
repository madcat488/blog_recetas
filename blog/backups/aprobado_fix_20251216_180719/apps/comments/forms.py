from django import forms
from .models import Comentario

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu comentario aquí...',
                'maxlength': 1000,
            }),
        }
    
    def clean_contenido(self):
        contenido = self.cleaned_data.get('contenido', '').strip()
        if len(contenido) < 10:
            raise forms.ValidationError('El comentario debe tener al menos 10 caracteres.')
        if len(contenido) > 1000:
            raise forms.ValidationError('El comentario no puede exceder los 1000 caracteres.')
        return contenido

class ModerarComentarioForm(forms.ModelForm):
    """Formulario para moderar comentarios"""
    class Meta:
        model = Comentario
        fields = ['estado', 'motivo_rechazo']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'motivo_rechazo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explica por qué rechazas este comentario (opcional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limitar opciones según permisos
        if user and not (user.is_superuser or user.is_staff):
            self.fields['estado'].choices = [
                ('aprobado', 'Aprobado'),
                ('rechazado', 'Rechazado'),
            ]