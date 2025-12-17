# apps/posts/forms.py
from django import forms
from .models import Post, Categoria
from django.core.exceptions import ValidationError


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'titulo', 'resumen', 'contenido', 'imagen', 'categoria',
            'ubicacion_pais', 'ubicacion_ciudad', 'mejor_epoca',
            'precio_aproximado', 'dificultad', 'duracia_recomendada',
            'palabras_clave', 'estado', 'visibilidad'
        ]
        widgets = {
            'resumen': forms.Textarea(attrs={'rows': 3, 'maxlength': 300}),
            'contenido': forms.Textarea(attrs={'rows': 10}),
            'dificultad': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'visibilidad': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Ordenar categorías alfabéticamente
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nombre')
        
        # Restringir opciones de estado según el usuario
        if user:
            if not (user.is_staff or user.is_superuser):
                self.fields['estado'].choices = [
                    ('borrador', 'Borrador'),
                    ('revision', 'En revisión'),
                ]
    
    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if len(titulo) < 5:
            raise ValidationError('El título debe tener al menos 5 caracteres.')
        return titulo
    
    def clean_contenido(self):
        contenido = self.cleaned_data.get('contenido')
        if len(contenido) < 50:
            raise ValidationError('La descripción debe tener al menos 50 caracteres.')
        return contenido

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'imagen', 'icono', 'color']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Aventura, Playa, Cultural...'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe esta categoría...'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'icono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'bi-globe, bi-mountain, bi-water, etc.'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'style': 'height: 40px;'
            }),
        }
        labels = {
            'nombre': 'Nombre de la categoría',
            'descripcion': 'Descripción',
            'imagen': 'Imagen representativa',
            'icono': 'Icono (opcional)',
            'color': 'Color representativo',
        }
        help_texts = {
            'icono': 'Visita <a href="https://icons.getbootstrap.com/" target="_blank">Bootstrap Icons</a> para ver nombres disponibles',
            'color': 'Selecciona un color que represente esta categoría',
        }

class PostBusquedaForm(forms.Form):
    """
    Formulario para buscar posts
    """
    buscador = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar viajes...',
            'aria-label': 'Buscar'
        }),
        label='',
        max_length=100
    )
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Filtrar por categoría'
    )
    
    orden = forms.ChoiceField(
        choices=[
            ('-fecha_publicacion', 'Más recientes'),
            ('fecha_publicacion', 'Más antiguos'),
            ('titulo', 'A-Z'),
            ('-titulo', 'Z-A'),
        ],
        required=False,
        initial='-fecha_publicacion',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Ordenar por'
    )

class PostFiltroForm(forms.Form):
    """
    Formulario para filtrar posts en el dashboard
    """
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('publicado', 'Publicados'),
        ('borrador', 'Borradores'),
    ]
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm'
        })
    )
    
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date'
        }),
        label='Desde'
    )
    
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date'
        }),
        label='Hasta'
    )