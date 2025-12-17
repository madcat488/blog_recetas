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
    class Meta:
        model = Comentario
        fields = ['estado', 'motivo_rechazo']
        widgets = {
            'estado': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'motivo_rechazo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ej: Contiene información incorrecta, lenguaje inapropiado, spam, etc.'
            }),
        }
        labels = {
            'estado': 'Cambiar estado a',
            'motivo_rechazo': 'Motivo (opcional)'
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Personalizar choices según el estado actual
        if self.instance and self.instance.estado == 'aprobado':
            self.fields['estado'].choices = [
                ('aprobado', '✅ Mantener aprobado'),
                ('rechazado', '❌ Rechazar'),
                ('pendiente', '⏳ Volver a pendiente'),
            ]
        elif self.instance and self.instance.estado == 'rechazado':
            self.fields['estado'].choices = [
                ('rechazado', '❌ Mantener rechazado'),
                ('aprobado', '✅ Aprobar'),
                ('pendiente', '⏳ Volver a pendiente'),
            ]
        else:
            self.fields['estado'].choices = [
                ('pendiente', '⏳ Mantener pendiente'),
                ('aprobado', '✅ Aprobar'),
                ('rechazado', '❌ Rechazar'),
            ]
    
    def clean(self):
        cleaned_data = super().clean()
        estado = cleaned_data.get('estado')
        motivo_rechazo = cleaned_data.get('motivo_rechazo')
        
        # Validar que si se rechaza, haya motivo
        if estado == 'rechazado' and not motivo_rechazo:
            self.add_error('motivo_rechazo', 
                        'Debes proporcionar un motivo al rechazar un comentario.')
        
        # Si no es rechazo, limpiar el motivo
        if estado != 'rechazado' and motivo_rechazo:
            cleaned_data['motivo_rechazo'] = ''
        
        return cleaned_data