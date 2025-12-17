# apps/usuarios/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from django.core.exceptions import ValidationError
from datetime import date


User = get_user_model()

class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@correo.com'
        }),
        label='Correo electrónico'
    )
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        }),
        label='Nombre de usuario',
        help_text='Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.'
    )
    
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        }),
        label='Nombre'
    )
    
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido'
        }),
        label='Apellido'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar clases Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            
            # Placeholders específicos para campos de contraseña
            if field_name == 'password1':
                field.widget.attrs['placeholder'] = 'Contraseña'
                field.help_text = '''
                    Requisitos de la contraseña:
                Tu contraseña no puede ser demasiado similar a tu otra información personal.
                    Tu contraseña debe contener al menos 8 caracteres.
                    Tu contraseña no puede ser una contraseña comúnmente utilizada.
                    Tu contraseña no puede ser enteramente numérica
                '''
            elif field_name == 'password2':
                field.widget.attrs['placeholder'] = 'Confirmar contraseña'
                field.label = 'Confirmación de contraseña'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        return username

class EditarPerfilForm(forms.ModelForm):
    # Campos adicionales que no están en el modelo
    telefono = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+54 9 11 1234-5678'
        }),
        label='Teléfono'
    )
    
    sitio_web = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://misitio.com'
        }),
        label='Sitio web'
    )
    
    biografia = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Cuéntanos sobre ti...',
            'rows': 4
        }),
        label='Biografía',
        max_length=500
    )
    
    class Meta:
        model = User
        fields = [
            'first_name', 
            'last_name', 
            'email', 
            'imagen',
            'telefono',
            'sitio_web',
            'biografia',
            'colaborador'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu apellido'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'colaborador': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'imagen': 'Foto de perfil',
            'colaborador': 'Soy colaborador',
        }
        
        help_texts = {
            'imagen': 'Formatos aceptados: JPG, PNG, GIF. Tamaño máximo: 2MB.',
            'colaborador': 'Los colaboradores pueden crear y gestionar contenido.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer el email requerido
        self.fields['email'].required = True
        
        # Solo staff puede cambiar el campo colaborador
        if 'colaborador' in self.fields:
            user = kwargs.get('instance')
            if user and not user.is_staff and not user.is_superuser:
                self.fields['colaborador'].disabled = True
                self.fields['colaborador'].help_text = 'Contacta con un administrador para solicitar ser colaborador.'
        
        # Agregar clases a todos los campos
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                else:
                    field.widget.attrs['class'] = 'form-control'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Verificar si el email ya existe (excluyendo el usuario actual)
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Este correo electrónico ya está en uso por otro usuario.')
        return email
    
    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen:
            # Validar tamaño de la imagen (2MB máximo)
            if imagen.size > 2 * 1024 * 1024:  # 2MB
                raise ValidationError('La imagen no puede pesar más de 2MB.')
            
            # Validar tipo de archivo
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            extension = imagen.name.split('.')[-1].lower()
            if extension not in allowed_extensions:
                raise ValidationError(
                    f'Formato de imagen no válido. Formatos aceptados: {", ".join(allowed_extensions)}'
                )
        
        return imagen

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Formulario personalizado para cambiar contraseña con estilos Bootstrap
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar clases Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f'Ingresa tu {field.label.lower()}'
            
            # Agregar iconos
            if field_name == 'old_password':
                field.widget.attrs['placeholder'] = 'Contraseña actual'
                field.label = 'Contraseña actual'
            elif field_name == 'new_password1':
                field.widget.attrs['placeholder'] = 'Nueva contraseña'
                field.label = 'Nueva contraseña'
                field.help_text = '''
                <div class="small text-muted mt-2">
                    <p class="mb-1">Tu contraseña debe cumplir con:</p>
                    <ul class="mb-0">
                        <li>Mínimo 8 caracteres de longitud</li>
                        <li>No puede ser similar a tu información personal</li>
                        <li>No puede ser una contraseña comúnmente utilizada</li>
                        <li>No puede ser enteramente numérica</li>
                    </ul>
                </div>
                '''
            elif field_name == 'new_password2':
                field.widget.attrs['placeholder'] = 'Confirmar nueva contraseña'
                field.label = 'Confirmar nueva contraseña'
    
    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError('La contraseña actual es incorrecta.')
        return old_password

class PerfilBusquedaForm(forms.Form):
    """
    Formulario para buscar usuarios (opcional, para admin)
    """
    username = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre de usuario...'
        }),
        label=''
    )
    
    rol = forms.ChoiceField(
        choices=[
            ('', 'Todos los roles'),
            ('admin', 'Administradores'),
            ('staff', 'Staff'),
            ('colaborador', 'Colaboradores'),
            ('usuario', 'Usuarios normales'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Filtrar por rol'
    )
    
    estado = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('activo', 'Activos'),
            ('inactivo', 'Inactivos'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Filtrar por estado'
    )
class RegistroUsuarioForm(UserCreationForm):
    # Personaliza los mensajes de error si es necesario
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        }),
        help_text="Mínimo 8 caracteres, incluir letras y números."
    )
    
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repita su contraseña'
        })
    )

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'nombre', 'apellido', 
            'fecha_nacimiento', 'imagen', 'password1', 'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@email.com'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu apellido'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': date.today().strftime('%Y-%m-%d')  # Evita fechas futuras
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'imagen': 'Foto de perfil',
        }
        help_texts = {
            'username': 'Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.',
        }

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        
        if fecha_nacimiento:
            # Calcular edad
            hoy = date.today()
            edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            
            # Verificar si es mayor de 13 años
            if edad < 13:
                raise ValidationError('Debes tener al menos 13 años para registrarte.')
            
            # Verificar que no sea una fecha futura
            if fecha_nacimiento > hoy:
                raise ValidationError('La fecha de nacimiento no puede ser futura.')
        
        return fecha_nacimiento

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        
        if imagen:
            # Validar tamaño máximo (2MB)
            max_size = 2 * 1024 * 1024  # 2MB en bytes
            if imagen.size > max_size:
                raise ValidationError('La imagen no puede superar los 2MB.')
            
            # Validar extensiones
            extensiones_validas = ['jpg', 'jpeg', 'png', 'gif']
            ext = imagen.name.split('.')[-1].lower()
            if ext not in extensiones_validas:
                raise ValidationError('Formato no válido. Use JPG, PNG o GIF.')
        
        return imagen